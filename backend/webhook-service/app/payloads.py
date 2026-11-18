import hashlib
import hmac
import json
from datetime import datetime, timezone

from shared.auth import AuthError
from shared.config import settings

MAX_WEBHOOK_BYTES = 1024 * 1024


def parse_and_verify(platform, raw, signature):
    if len(raw) > MAX_WEBHOOK_BYTES:
        raise AuthError(413, "PAYLOAD_TOO_LARGE", "Webhook vượt giới hạn 1 MiB")
    if platform == "FACEBOOK":
        if not settings.facebook_enabled or not settings.fb_app_secret:
            raise AuthError(503, "CONFIG_REQUIRED", "Webhook Facebook chưa được cấu hình")
        expected = "sha256=" + hmac.new(settings.fb_app_secret.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest((signature or "").encode(), expected.encode()):
            raise AuthError(403, "INVALID_SIGNATURE", "Chữ ký webhook không hợp lệ")
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError
    except (ValueError, UnicodeError):
        raise AuthError(400, "INVALID_PAYLOAD", "Webhook phải là JSON object hợp lệ") from None
    if platform == "ZALO":
        if not settings.zalo_enabled or not all((settings.zalo_app_id, settings.zalo_webhook_secret)):
            raise AuthError(503, "CONFIG_REQUIRED", "Webhook Zalo chưa được cấu hình")
        timestamp = payload.get("timestamp")
        if str(payload.get("app_id")) != settings.zalo_app_id or not isinstance(timestamp, (str, int)):
            raise AuthError(403, "INVALID_SIGNATURE", "Ứng dụng hoặc timestamp không hợp lệ")
        digest = hashlib.sha256(settings.zalo_app_id.encode() + raw + str(timestamp).encode() +
                                settings.zalo_webhook_secret.encode()).hexdigest()
        header = (signature or "").removeprefix("mac=")
        if not hmac.compare_digest(header.encode(), digest.encode()):
            raise AuthError(403, "INVALID_SIGNATURE", "Chữ ký webhook không hợp lệ")
    return payload


def identity(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 255:
        raise ValueError("Invalid provider identity")
    return value


def normalized(platform, account, sender, mid, text, timestamp):
    stamp = datetime.fromtimestamp(int(timestamp) / 1000, timezone.utc)
    if not isinstance(text, str) or not text or len(text) > 10000:
        raise ValueError("Invalid text")
    return {"platform": platform, "account_id": identity(account), "user_id": identity(sender),
            "event_id": identity(mid), "text": text, "occurred_at": stamp.isoformat()}


def messages(platform, payload):
    try:
        rows = []
        if platform == "FACEBOOK":
            if payload.get("object") != "page" or not isinstance(payload.get("entry"), list):
                raise ValueError
            for entry in payload["entry"]:
                account = identity(entry["id"])
                for event in entry.get("messaging", []):
                    message = event.get("message", {})
                    if message.get("is_echo"):
                        continue
                    if "message" not in event:
                        if "postback" not in event:
                            continue
                        postback = event["postback"]
                        message = {
                            "mid": postback.get("mid") or "postback:" + hashlib.sha256(
                                json.dumps(event, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                            "text": postback.get("title") or postback.get("payload") or "[Tương tác Facebook]",
                        }
                    if event["recipient"]["id"] != account:
                        raise ValueError
                    text = message.get("text") or "[Tin đính kèm từ Facebook]"
                    rows.append(normalized(platform, account, event["sender"]["id"], message["mid"], text, event["timestamp"]))
        elif str(payload.get("event_name", "")).startswith("user_send_"):
            message = payload["message"]
            rows.append(normalized(platform, payload["recipient"]["id"], payload["sender"]["id"],
                message["msg_id"], message.get("text") or "[Tin đính kèm từ Zalo]", payload["timestamp"]))
        if len(rows) > 1000:
            raise ValueError
        return rows
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError, OSError):
        raise AuthError(400, "INVALID_PAYLOAD", "Cấu trúc sự kiện nền tảng không hợp lệ") from None
