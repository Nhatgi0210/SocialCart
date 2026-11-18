import hashlib
import json
import secrets
from uuid import uuid4

from fastapi import Header, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert

from app.payloads import MAX_WEBHOOK_BYTES, messages, parse_and_verify
from app.worker import incoming_worker
from shared.auth import AuthError
from shared.config import settings
from shared.db.models import WebhookOutbox, WebhookReceipt
from shared.inbox_http import DB, inbox_service

app, _seller = inbox_service("webhook-service", background=(incoming_worker,))


@app.get("/webhooks/facebook")
async def verify(mode: str = Query(alias="hub.mode"), token: str = Query(alias="hub.verify_token"),
                 challenge: str = Query(alias="hub.challenge", max_length=2000)):
    if not settings.facebook_enabled or not settings.fb_webhook_verify_token:
        raise AuthError(503, "CONFIG_REQUIRED", "Cần cấu hình verify token Facebook")
    if mode != "subscribe" or not secrets.compare_digest(token.encode(), settings.fb_webhook_verify_token.encode()):
        raise AuthError(403, "FORBIDDEN", "Verify token không hợp lệ")
    return PlainTextResponse(challenge)


async def receive(platform, request, signature, db):
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_WEBHOOK_BYTES:
            raise AuthError(413, "PAYLOAD_TOO_LARGE", "Webhook vượt giới hạn 1 MiB")
        raw.extend(chunk)
    raw = bytes(raw)
    payload = parse_and_verify(platform, raw, signature)
    events = messages(platform, payload)
    configured_account = settings.fb_page_id if platform == "FACEBOOK" else settings.zalo_oa_id
    if any(event["account_id"] != configured_account for event in events):
        raise AuthError(403, "ACCOUNT_MISMATCH", "Sự kiện không thuộc Page/OA đã cấu hình")
    if not events:
        # Retain signed events we do not consume, without scheduling text work.
        events = [{"account_id": configured_account or "unconfigured",
                   "event_id": "ignored:" + hashlib.sha256(raw).hexdigest()}]
    for event in sorted(events, key=lambda event: (event["account_id"], event["event_id"])):
        candidate = str(uuid4())
        stmt = insert(WebhookReceipt).values(id=candidate, platform=platform, account_id=event["account_id"],
            event_id=event["event_id"], raw_payload=raw.decode("utf-8"), processed="text" not in event)
        await db.execute(stmt.on_duplicate_key_update(id=WebhookReceipt.id))
        receipt = await db.scalar(select(WebhookReceipt).where(WebhookReceipt.platform == platform,
            WebhookReceipt.account_id == event["account_id"], WebhookReceipt.event_id == event["event_id"]))
        if receipt.id == candidate and "text" in event:
            db.add(WebhookOutbox(platform=platform, receipt_id=candidate, payload=json.dumps(event, ensure_ascii=False)))
    await db.commit()
    return {"status": "ok"}


@app.post("/webhooks/facebook")
async def facebook(request: Request, db: DB, x_hub_signature_256: str | None = Header(default=None)):
    return await receive("FACEBOOK", request, x_hub_signature_256, db)


@app.post("/webhooks/zalo")
async def zalo(request: Request, db: DB, x_zevent_signature: str | None = Header(default=None)):
    return await receive("ZALO", request, x_zevent_signature, db)
