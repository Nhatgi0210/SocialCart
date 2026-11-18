"""Provider wire formats under HTTP mocks, without external delivery."""
import importlib.util
import json

import httpx
import pytest

from shared.config import settings
from tests.conftest import BACKEND

spec = importlib.util.spec_from_file_location("provider_adapters_under_test", BACKEND / "platform-service/app/providers.py")
providers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(providers)


@pytest.mark.asyncio
async def test_text_adapter_and_oauth_refresh_wire(monkeypatch):
    monkeypatch.setattr(settings, "fb_graph_version", "v27.0")
    requests = []
    scenario = {"mode": "sent"}
    def handle(request):
        requests.append(request)
        if scenario["mode"] == "timeout":
            raise httpx.ReadTimeout("simulated read timeout")
        if scenario["mode"] == "connect":
            raise httpx.ConnectError("simulated connect failure")
        if scenario["mode"] == "rejected":
            return httpx.Response(400, json={"error": {"code": 200}})
        if request.url.host == "oauth.zaloapp.com":
            assert request.headers["secret_key"] == "zalo-local-secret"
            assert b"grant_type=refresh_token" in request.content
            return httpx.Response(200, json={"access_token": "rotated-access", "refresh_token": "rotated-refresh", "expires_in": "90000"})
        if request.url.host == "graph.facebook.com":
            assert request.headers["Authorization"] == "Bearer local-provider-token"
            assert json.loads(request.content) == {"recipient": {"id": "test-user"}, "message": {"text": "Xin chào"},
                                                  "messaging_type": "RESPONSE"}
            return httpx.Response(200, json={"message_id": "facebook-msg"})
        assert request.headers["access_token"] == "local-provider-token"
        assert json.loads(request.content) == {"recipient": {"user_id": "test-user"}, "message": {"text": "Xin chào"}}
        return httpx.Response(200, json={"error": 0, "data": {"message_id": "zalo-msg"}})
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs))
    for platform in ("FACEBOOK", "ZALO"):
        assert (await providers.send_text(platform, "test-page", "test-user", "local-provider-token", "Xin chào"))["accepted"]
    scenario["mode"] = "rejected"
    result = await providers.send_text("FACEBOOK", "test-page", "test-user", "local-provider-token", "Xin chào")
    assert result["error_code"] == "FACEBOOK_200" and not result["delivery_unknown"]
    scenario["mode"] = "timeout"
    assert (await providers.send_text("ZALO", "test-oa", "test-user", "local-provider-token", "Xin chào"))["delivery_unknown"]
    scenario["mode"] = "connect"
    assert (await providers.send_text("ZALO", "test-oa", "test-user", "local-provider-token", "Xin chào"))["error_code"] == "CONNECTION_FAILED"
    scenario["mode"] = "sent"
    monkeypatch.setattr(settings, "zalo_app_secret", "zalo-local-secret")
    result = await providers.refresh_zalo("old-refresh")
    assert result["refresh_token"] == "rotated-refresh"
    assert len(requests) == 6


@pytest.mark.asyncio
async def test_facebook_code_exchange_requires_permissions_and_page_subscription(monkeypatch):
    for key, value in {"facebook_enabled": True, "fb_app_id": "test-app", "fb_app_secret": "test-secret",
                       "fb_page_id": "test-page", "fb_graph_version": "v27.0"}.items():
        monkeypatch.setattr(settings, key, value)
    called = []
    def handle(request):
        called.append(request.url.path)
        if request.url.path.endswith("/oauth/access_token"):
            return httpx.Response(200, json={"access_token": "user-token"})
        if request.url.path.endswith("/me/permissions"):
            return httpx.Response(200, json={"data": [
                {"permission": permission, "status": "granted"} for permission in providers.FB_SCOPES.split(",")
            ]})
        if request.url.path.endswith("/me/accounts"):
            return httpx.Response(200, json={"data": [
                {"id": "test-page", "name": "Page test", "access_token": "page-token", "tasks": ["MESSAGING"]},
            ]})
        assert request.url.path.endswith("/test-page/subscribed_apps")
        assert request.headers["Authorization"] == "Bearer page-token"
        return httpx.Response(200, json={"success": True})
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs))
    result = await providers.exchange("facebook", "local-code", "local-verifier")
    assert result == {"account_id": "test-page", "name": "Page test", "access_token": "page-token"}
    assert len(called) == 4
