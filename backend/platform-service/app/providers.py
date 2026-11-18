import hashlib
import base64
import re
from urllib.parse import urlencode, quote

import httpx

from shared.auth import AuthError
from shared.config import settings

FB_SCOPES = "pages_show_list,pages_messaging,pages_manage_metadata"


def require_platform(platform):
    enabled = settings.facebook_enabled if platform == "facebook" else settings.zalo_enabled
    values = (settings.fb_app_id, settings.fb_app_secret, settings.fb_page_id, settings.fb_graph_version) if platform == "facebook" else (
        settings.zalo_app_id, settings.zalo_app_secret, settings.zalo_oa_id)
    if not enabled or not all(values):
        raise AuthError(503, "CONFIG_REQUIRED", "Cần bật và cấu hình App cùng Page/OA ở backend")
    if platform == "facebook" and not re.fullmatch(r"v[0-9]+\.0", settings.fb_graph_version):
        raise AuthError(503, "CONFIG_REQUIRED", "FB_GRAPH_VERSION cần đúng phiên bản Graph API đã kiểm")


def callback_url(platform):
    return settings.public_api_url.rstrip("/") + f"/api/v1/connections/{platform}/oauth/callback"


def authorization_url(platform, state, verifier):
    require_platform(platform)
    callback = callback_url(platform)
    if platform == "facebook":
        return f"https://www.facebook.com/{settings.fb_graph_version}/dialog/oauth?" + urlencode({
            "client_id": settings.fb_app_id, "redirect_uri": callback, "state": state,
            "scope": FB_SCOPES, "response_type": "code",
        })
    # OA Developers generates the consent link including the app's chosen permissions.
    template = settings.zalo_authorization_url
    if not template.startswith("https://oauth.zaloapp.com/") or not all(
        placeholder in template for placeholder in ("{state}", "{code_challenge}", "{redirect_uri}")
    ):
        raise AuthError(503, "CONFIG_REQUIRED", "Cần ZALO_AUTHORIZATION_URL từ màn hình cấp quyền, có state/challenge/callback")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    for key, value in {"state": state, "code_challenge": challenge, "redirect_uri": callback,
                       "app_id": settings.zalo_app_id}.items():
        template = template.replace("{" + key + "}", quote(value, safe=""))
    return template


async def provider_json(client, method, url, **kwargs):
    try:
        response = await client.request(method, url, **kwargs)
        result = response.json()
        if not isinstance(result, dict) or not response.is_success or result.get("error"):
            raise AuthError(503, "PROVIDER_REJECTED", "Nền tảng từ chối yêu cầu. Kiểm tra tài khoản và quyền đã cấp")
        return result
    except (httpx.HTTPError, ValueError, TypeError):
        raise AuthError(503, "PROVIDER_UNAVAILABLE", "Không xác định được kết quả từ nền tảng. Hãy kết nối lại") from None


async def exchange(platform, code, verifier):
    require_platform(platform)
    async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
        if platform == "facebook":
            graph = "https://graph.facebook.com/" + settings.fb_graph_version
            token = await provider_json(client, "GET", graph + "/oauth/access_token", params={
                "client_id": settings.fb_app_id, "client_secret": settings.fb_app_secret,
                "code": code, "redirect_uri": callback_url(platform),
            })
            user_token = token["access_token"]
            auth = {"Authorization": "Bearer " + user_token}
            permissions = await provider_json(client, "GET", graph + "/me/permissions", headers=auth)
            granted = {row["permission"] for row in permissions.get("data", []) if row.get("status") == "granted"}
            if not set(FB_SCOPES.split(",")).issubset(granted):
                raise AuthError(403, "PERMISSION_REQUIRED", "Cần cấp đủ quyền quản lý Page và nhắn tin")
            pages = await provider_json(client, "GET", graph + "/me/accounts",
                                        params={"fields": "id,name,access_token,tasks", "limit": 100}, headers=auth)
            page = next((row for row in pages.get("data", []) if row["id"] == settings.fb_page_id), None)
            if page is None or not page.get("access_token") or not set(page.get("tasks", [])) & {"MESSAGING", "MANAGE"}:
                raise AuthError(403, "PAGE_UNAVAILABLE", "Page đã cấu hình chưa có quyền nhắn tin trong tài khoản")
            subscription = await provider_json(client, "POST", graph + "/" + page["id"] + "/subscribed_apps",
                headers={"Authorization": "Bearer " + page["access_token"]},
                data={"subscribed_fields": "messages,messaging_postbacks"})
            if subscription.get("success") is not True:
                raise AuthError(503, "SUBSCRIPTION_FAILED", "Chưa đăng ký được webhook cho Page")
            return {"account_id": page["id"], "name": page["name"], "access_token": page["access_token"]}
        token = await provider_json(client, "POST", "https://oauth.zaloapp.com/v4/oa/access_token",
            headers={"secret_key": settings.zalo_app_secret},
            data={"app_id": settings.zalo_app_id, "code": code, "code_verifier": verifier, "grant_type": "authorization_code"})
        oa = await provider_json(client, "GET", "https://openapi.zalo.me/v2.0/oa/getoa",
                                 headers={"access_token": token["access_token"]})
        account_id = str(oa["data"].get("oaid") or oa["data"].get("oa_id", ""))
        if account_id != settings.zalo_oa_id:
            raise AuthError(403, "OA_MISMATCH", "OA được cấp quyền khác OA đã cấu hình")
        return {**token, "account_id": account_id, "name": oa["data"]["name"]}


async def refresh_zalo(refresh_token):
    async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
        return await provider_json(client, "POST", "https://oauth.zaloapp.com/v4/oa/access_token",
            headers={"secret_key": settings.zalo_app_secret}, data={
                "app_id": settings.zalo_app_id, "refresh_token": refresh_token, "grant_type": "refresh_token",
            })


async def send_text(platform, account_id, recipient_id, token, content):
    if len(content) > 2000:
        return {"accepted": False, "delivery_unknown": False, "error_code": "TEXT_TOO_LONG"}
    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            if platform == "FACEBOOK":
                response = await client.post(f"https://graph.facebook.com/{settings.fb_graph_version}/{account_id}/messages",
                    headers={"Authorization": "Bearer " + token}, json={
                        "recipient": {"id": recipient_id}, "message": {"text": content}, "messaging_type": "RESPONSE",
                    })
            else:
                response = await client.post("https://openapi.zalo.me/v3.0/oa/message/cs",
                    headers={"access_token": token}, json={"recipient": {"user_id": recipient_id}, "message": {"text": content}})
        result = response.json()
        provider_id = result.get("message_id") if platform == "FACEBOOK" else result.get("data", {}).get("message_id")
        if response.is_success and not result.get("error") and isinstance(provider_id, str) and provider_id:
            return {"accepted": True, "delivery_unknown": False, "provider_message_id": provider_id}
        if result.get("error") and response.status_code < 500:
            error = result["error"]
            code = str(error.get("code", "REJECTED") if isinstance(error, dict) else error)
            return {"accepted": False, "delivery_unknown": False, "error_code": platform + "_" + code[:50]}
        return {"accepted": False, "delivery_unknown": True, "error_code": "DELIVERY_UNKNOWN"}
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout):
        return {"accepted": False, "delivery_unknown": False, "error_code": "CONNECTION_FAILED"}
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return {"accepted": False, "delivery_unknown": True, "error_code": "DELIVERY_UNKNOWN"}
