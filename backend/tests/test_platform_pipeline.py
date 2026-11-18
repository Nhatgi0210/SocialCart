"""Real MySQL/Redis persistence with explicit simulated provider responses."""
import asyncio
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from alembic import command
from alembic.config import Config
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.exc import OperationalError

from shared.auth import AuthError, Sessions, issue_access, session_key
from shared.config import settings
from shared.db.models import AIConfig, Conversation, ConversationOutbox, Customer, Message, PlatformConnection, PlatformDispatch, WebhookOutbox, WebhookReceipt
from shared.db.session import get_session
from tests.conftest import BACKEND, load_service
from tests.test_auth import rsa_keys  # noqa: F401


@pytest.mark.asyncio
async def test_settings_webhook_delivery_and_oauth(monkeypatch, rsa_keys):
    url, cache = os.getenv("SC_TEST_DATABASE_URL"), os.getenv("SC_TEST_REDIS_URL")
    if not url or not cache:
        pytest.skip("Requires isolated MySQL/Redis")
    assert (make_url(url).database or "").startswith("socialcart_test_")
    assert make_url(cache).database == "15"
    for name, value in {
        "database_url": url, "redis_url": cache, "encryption_key": "11" * 32,
        "internal_service_token": "pipeline-local-test", "facebook_enabled": True,
        "fb_app_id": "test-app", "fb_app_secret": "test-secret", "fb_page_id": "test-page",
        "fb_graph_version": "v27.0", "fb_webhook_verify_token": "test-verify",
        "zalo_enabled": True, "zalo_app_id": "zalo-app", "zalo_oa_id": "test-oa",
        "zalo_webhook_secret": "zalo-webhook-test", "zalo_app_secret": "zalo-app-secret",
        "zalo_authorization_url": "https://oauth.zaloapp.com/v4/oa/permission?app_id={app_id}&state={state}&code_challenge={code_challenge}&redirect_uri={redirect_uri}",
    }.items():
        monkeypatch.setattr(settings, name, value)
    await asyncio.to_thread(command.upgrade, Config(str(BACKEND / "shared/db/alembic.ini")), "head")
    engine = create_async_engine(url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = Redis.from_url(cache, decode_responses=True)
    monkeypatch.setattr(Redis, "from_url", lambda *_args, **_kwargs: redis)
    services = {name: load_service(name) for name in (
        "ai-service", "webhook-service", "platform-service", "customer-service", "conversation-service", "api-gateway")}
    async def session():
        async with factory() as db:
            yield db
    for service in services.values():
        service.app.dependency_overrides[get_session] = session
    gateway = services["api-gateway"]
    monkeypatch.setattr(gateway, "get_redis", lambda: redis)
    web, platform, inbox = (services[name] for name in ("webhook-service", "platform-service", "conversation-service"))
    receipt_worker = web.incoming_worker.__globals__["deliver_one"]
    send_worker = inbox.outgoing_worker.__globals__["dispatch_one"]
    for work in (receipt_worker, send_worker, platform.refresh_one):
        monkeypatch.setitem(work.__globals__, "get_session_factory", lambda: factory)
    original_client = httpx.AsyncClient
    routes = {
        8000: gateway, 8001: services["ai-service"], 8002: inbox, 8003: services["customer-service"],
        8006: services["ai-service"], 8007: web, 8010: platform,
    }
    class Transport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            service = routes[request.url.port]
            return await httpx.ASGITransport(app=service.app).handle_async_request(request)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original_client(transport=Transport(), **kwargs))
    user, sid = str(uuid4()), str(uuid4())
    _, cookie, _ = await Sessions(redis).create(user, sid)
    bearer = {"Authorization": "Bearer " + issue_access(user, sid)}
    async def exchange(name, code, verifier):
        assert len(verifier) == 43
        return {"account_id": "test-page" if name == "facebook" else "test-oa",
                "name": "Page/OA simulated", "access_token": "private-provider-token",
                "refresh_token": "private-refresh-token", "expires_in": "90000"}
    monkeypatch.setattr(platform, "exchange", exchange)
    calls = []
    outcome = {"accepted": True, "delivery_unknown": False, "provider_message_id": "provider-" + uuid4().hex}
    async def send(*args):
        calls.append(args)
        return outcome
    monkeypatch.setattr(platform, "send_text", send)

    try:
        async with original_client(transport=Transport(), base_url="http://localhost:8000") as client:
            assert (await client.get("/api/v1/ai-config")).status_code == 401
            client.headers.update(bearer)
            config = "/api/v1/ai-config"
            assert (await client.get(config)).json()["data"] == {"order_timeout_seconds": 86400, "payment_template": None}
            assert (await client.put(config, json={"order_timeout_seconds": 0})).status_code == 422
            bank = {"bank_name": "Bank demo", "account_number": "123456", "account_holder": "NGUOI BAN"}
            assert (await client.put(config, json={"order_timeout_seconds": 7200, "payment_template": bank})).status_code == 200
            assert (await client.get(config)).json()["data"]["payment_template"] == bank
            assert (await client.put(config, json={"payment_template": None})).json()["data"]["payment_template"] is None
            faq_body = {"question": "Có size M?", "answer": "Có", "trigger_keywords": ["size M"]}
            faq = (await client.post(config + "/faqs", json=faq_body)).json()["data"]
            assert (await client.put(config + "/faqs/" + faq["id"], json={**faq_body, "answer": "Kiểm kho trước"})).status_code == 200
            assert (await client.get(config + "/faqs")).json()["data"][0]["answer"] == "Kiểm kho trước"
            assert (await client.delete(config + "/faqs/" + faq["id"])).status_code == 204
            assert (await client.get(config + "/faqs")).json()["data"] == []
            assert (await client.get("/internal/ai-config")).status_code == 404

            states = {}
            for name in ("facebook", "zalo"):
                start = await client.post(f"/api/v1/connections/{name}/oauth/start")
                assert start.status_code == 200, start.text
                authorization = start.json()["data"]["authorization_url"]
                state = parse_qs(urlsplit(authorization).query)["state"][0]
                states[name] = state
                callback = f"/api/v1/connections/{name}/oauth/callback"
                response = await client.get(callback, params={"state": state, "code": "test-code"}, headers={"Authorization": ""})
                assert response.status_code == 302, response.text
                assert (await client.get(callback, params={"state": state, "code": "test-code"})).status_code == 403
            listed = (await client.get("/api/v1/connections")).json()["data"]
            assert len(listed) == 2 and all(row["status"] == "CONNECTED" for row in listed)
            assert "private-" not in json.dumps(listed)
            async with factory() as db:
                connection = await db.scalar(select(PlatformConnection).where(PlatformConnection.platform == "FACEBOOK"))
                assert connection.encrypted_access_token != "private-provider-token"

            webhook_path = "/webhooks/facebook"
            assert (await client.get(webhook_path, params={"hub.mode": "subscribe", "hub.verify_token": "test-verify",
                                                          "hub.challenge": "000abc"})).text == "000abc"
            incoming_id = "incoming-" + uuid4().hex
            payload = {"object": "page", "entry": [{"id": "test-page", "messaging": [{
                "sender": {"id": "customer-test"}, "recipient": {"id": "test-page"}, "timestamp": 1794978000000,
                "message": {"mid": incoming_id, "text": "Tin đến mô phỏng"},
            }]}]}
            raw = json.dumps(payload, ensure_ascii=False).encode()
            signature = "sha256=" + hmac.new(b"test-secret", raw, hashlib.sha256).hexdigest()
            assert (await client.post(webhook_path, content=raw, headers={"X-Hub-Signature-256": "wrong"})).status_code == 403
            assert (await client.post(webhook_path, content=raw + b" ", headers={"X-Hub-Signature-256": signature})).status_code == 403
            async def unavailable_db():
                raise OperationalError("hidden SQL", {}, Exception("simulated"))
                yield
            web.app.dependency_overrides[get_session] = unavailable_db
            assert (await client.post(webhook_path, content=raw, headers={"X-Hub-Signature-256": signature})).status_code == 503
            web.app.dependency_overrides[get_session] = session
            responses = await asyncio.gather(*(client.post(webhook_path, content=raw,
                            headers={"X-Hub-Signature-256": signature}) for _ in range(2)))
            assert all(response.status_code == 200 for response in responses), [response.text for response in responses]
            async with factory() as db:
                assert await db.scalar(select(func.count()).select_from(WebhookReceipt).where(WebhookReceipt.event_id == incoming_id)) == 1
                assert not await db.scalar(select(Message.id).where(Message.platform_msg_id == incoming_id))
            # Backend outage keeps the durable job pending and schedules recovery.
            original_url = settings.customer_service_url
            monkeypatch.setattr(settings, "customer_service_url", "http://127.0.0.1:8007/not-an-internal-route")
            assert await receipt_worker() is False
            monkeypatch.setattr(settings, "customer_service_url", original_url)
            async with factory.begin() as db:
                job = await db.scalar(select(WebhookOutbox).where(WebhookOutbox.platform == "FACEBOOK").with_for_update())
                assert job.attempt_count == 1 and job.status == "PENDING"
                job.next_attempt_at = None
            assert await receipt_worker()
            async with factory() as db:
                received = await db.scalar(select(Message).where(Message.platform_msg_id == incoming_id))
                conv_id = received.conversation_id
                conversation = await db.get(Conversation, conv_id)
                assert conversation.ai_status == "NEEDS_SELLER" and not conversation.is_read
                assert await db.scalar(select(func.count()).select_from(Customer).where(Customer.platform_user_id == "customer-test")) == 1
            assert (await client.post(webhook_path, content=raw, headers={"X-Hub-Signature-256": signature})).status_code == 200
            assert not await receipt_worker()

            zalo_payload = {"app_id": "zalo-app", "recipient": {"id": "test-oa"}, "sender": {"id": "zalo-customer"},
                "event_name": "user_send_text", "message": {"msg_id": "zalo-" + uuid4().hex, "text": "Tin từ OA"},
                "timestamp": "1794978000000"}
            raw_zalo = json.dumps(zalo_payload).encode()
            sig_zalo = hashlib.sha256(b"zalo-app" + raw_zalo + b"1794978000000" + b"zalo-webhook-test").hexdigest()
            assert (await client.post("/webhooks/zalo", content=raw_zalo)).status_code == 403
            assert (await client.post("/webhooks/zalo", content=raw_zalo, headers={"X-ZEvent-Signature": "mac=" + sig_zalo})).status_code == 200
            assert await receipt_worker()
            path = "/api/v1/conversations/" + conv_id + "/messages"
            key = str(uuid4())
            messages = await asyncio.gather(*(client.post(path, json={"content": "Phản hồi demo"},
                headers={"Idempotency-Key": key}) for _ in range(2)))
            assert [response.status_code for response in messages] == [202, 202], [r.text for r in messages]
            outgoing = messages[0].json()["data"]
            assert messages[0].json() == messages[1].json() and outgoing["status"] == "SENDING"
            assert await send_worker()
            async with factory() as db:
                saved = await db.get(Message, outgoing["id"])
                assert saved.status == "SENT" and not saved.delivery_unknown
                conv = await db.get(Conversation, conv_id)
                assert conv.ai_status == "SELLER_HANDLING"
                attempt = await db.scalar(select(PlatformDispatch).where(PlatformDispatch.message_id == outgoing["id"]))
            # Replaying the same platform attempt never calls the provider a second time.
            async with original_client(transport=httpx.ASGITransport(app=platform.app), base_url="http://platform") as direct:
                replay = await direct.post(f"/internal/messages/{outgoing['id']}/dispatch",
                    json={"attempt_id": attempt.id}, headers={"Authorization": "Bearer pipeline-local-test"})
                assert replay.status_code == 200
            assert len(calls) == 1
            outcome = {"accepted": False, "delivery_unknown": False, "error_code": "FACEBOOK_200"}
            failed = (await client.post(path, json={"content": "Phản hồi lỗi"}, headers={"Idempotency-Key": str(uuid4())})).json()["data"]
            assert await send_worker()
            async with factory() as db:
                assert (await db.get(Message, failed["id"])).status == "FAILED"
            retry_path = path + "/" + failed["id"] + "/retry"
            retry = await client.post(retry_path, headers={"Idempotency-Key": str(uuid4())})
            assert retry.status_code == 202 and retry.json()["data"]["id"] == failed["id"]
            outcome = {"accepted": False, "delivery_unknown": True, "error_code": "DELIVERY_UNKNOWN"}
            assert await send_worker()
            assert (await client.post(retry_path, headers={"Idempotency-Key": str(uuid4())})).status_code == 409
            assert not await send_worker()
            interrupted = (await client.post(path, json={"content": "Tin đã claim trước crash"},
                headers={"Idempotency-Key": str(uuid4())})).json()["data"]
            before_calls = len(calls)
            async with factory.begin() as db:
                message = await db.get(Message, interrupted["id"])
                message.delivery_unknown, message.error_code = True, "DISPATCH_IN_PROGRESS"
                job = await db.scalar(select(ConversationOutbox).where(ConversationOutbox.message_id == message.id))
                job.next_attempt_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
            assert await send_worker()
            assert len(calls) == before_calls
            async with factory() as db:
                assert (await db.get(Message, interrupted["id"])).status == "FAILED"
            calls_before = len(calls)
            outcome = {"accepted": False, "delivery_unknown": False, "error_code": "CONNECTION_FAILED"}
            safe_retry = (await client.post(path, json={"content": "Thử lại khi chưa kết nối được"},
                headers={"Idempotency-Key": str(uuid4())})).json()["data"]
            for attempt in range(3):
                assert await send_worker()
                async with factory.begin() as db:
                    job = await db.scalar(select(ConversationOutbox).where(ConversationOutbox.message_id == safe_retry["id"]))
                    assert job.attempt_count == attempt + 1
                    job.next_attempt_at = None
            assert len(calls) == calls_before + 3
            assert not await send_worker()
            async with factory.begin() as db:
                connection = await db.scalar(select(PlatformConnection).where(PlatformConnection.platform == "ZALO"))
                connection.token_expires_at = datetime.now(timezone.utc).replace(tzinfo=None)
            async def rotate(_refresh):
                return {"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": "90000"}
            monkeypatch.setattr(platform, "refresh_zalo", rotate)
            assert await platform.refresh_one()
            assert not await platform.refresh_one()
            async with factory.begin() as db:
                connection = await db.scalar(select(PlatformConnection).where(PlatformConnection.platform == "ZALO"))
                assert platform.decrypt(connection.encrypted_refresh_token) == "new-refresh"
                connection.token_expires_at = datetime.now(timezone.utc).replace(tzinfo=None)
            async def uncertain_refresh(_refresh):
                raise AuthError(503, "PROVIDER_UNAVAILABLE", "simulated")
            monkeypatch.setattr(platform, "refresh_zalo", uncertain_refresh)
            assert not await platform.refresh_one()
            assert not await platform.refresh_one()
            async with factory() as db:
                connection = await db.scalar(select(PlatformConnection).where(PlatformConnection.platform == "ZALO"))
                assert connection.status == "ERROR" and connection.last_error_code == "REFRESH_IN_PROGRESS"
            assert (await client.delete("/api/v1/connections/facebook")).status_code == 204
            async with factory() as db:
                row = await db.scalar(select(PlatformConnection).where(PlatformConnection.platform == "FACEBOOK"))
                assert row.encrypted_access_token is None and row.status == "DISCONNECTED"

            state = (await client.post("/api/v1/connections/facebook/oauth/start")).json()["data"]["authorization_url"]
            state = parse_qs(urlsplit(state).query)["state"][0]
            await Sessions(redis).logout(cookie, bearer["Authorization"])
            callback = await client.get("/api/v1/connections/facebook/oauth/callback", params={"state": state, "code": "test"})
            assert callback.status_code == 403
    finally:
        for service in services.values():
            service.app.dependency_overrides.clear()
        await redis.delete(session_key(sid))
        await redis.aclose()
        await engine.dispose()
