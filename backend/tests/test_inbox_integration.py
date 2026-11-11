"""Exercise the customer and inbox routes with isolated MySQL and Redis."""
import asyncio
import os
import sys
from uuid import uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from shared.auth import Sessions, issue_access, session_key
from shared.config import settings
from shared.db.models import Conversation
from shared.db.session import get_session
from tests.conftest import BACKEND, load_service
from tests.test_auth import rsa_keys  # noqa: F401


@pytest.mark.asyncio
async def test_customer_and_inbox_through_gateway(monkeypatch, rsa_keys):
    url, cache = os.getenv("SC_TEST_DATABASE_URL"), os.getenv("SC_TEST_REDIS_URL")
    if not url or not cache:
        pytest.skip("Requires isolated MySQL and Redis")
    assert (make_url(url).database or "").startswith("socialcart_test_")
    assert make_url(cache).database == "15"
    monkeypatch.setattr(settings, "database_url", url)
    monkeypatch.setattr(settings, "internal_service_token", "local-test-service-token")
    await asyncio.to_thread(command.upgrade, Config(str(BACKEND / "shared/db/alembic.ini")), "head")

    async def seed():
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-X", "utf8", str(BACKEND.parent / "scripts/seed-inbox-demo.py"),
            env={**os.environ, "APP_ENV": "local", "DATABASE_URL": url},
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        _, err = await process.communicate()
        assert process.returncode == 0, err.decode()

    await seed()
    redis = Redis.from_url(cache, decode_responses=True)
    engine = create_async_engine(url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def db_session():
        async with factory() as session:
            yield session

    monkeypatch.setattr(Redis, "from_url", lambda *_args, **_kwargs: redis)
    customer = load_service("customer-service")
    inbox = load_service("conversation-service")
    gateway = load_service("api-gateway")
    monkeypatch.setattr(gateway, "get_redis", lambda: redis)
    for service in (customer, inbox):
        service.app.dependency_overrides[get_session] = db_session

    class Upstream(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            app = customer.app if request.url.path.startswith("/api/v1/customers") else inbox.app
            return await httpx.ASGITransport(app=app).handle_async_request(request)

    original_client = httpx.AsyncClient
    monkeypatch.setattr(gateway.httpx, "AsyncClient", lambda **kwargs: original_client(transport=Upstream(), **kwargs))
    uid, sid = str(uuid4()), str(uuid4())
    await Sessions(redis).create(uid, sid)
    headers = {"Authorization": "Bearer " + issue_access(uid, sid)}
    try:
        async with original_client(transport=httpx.ASGITransport(app=gateway.app), base_url="http://localhost:8000") as client:
            assert (await client.get("/api/v1/customers")).status_code == 401
            assert (await client.post("/internal/customers/upsert", headers=headers)).status_code == 404
            client.headers.update(headers)
            response = await client.get("/api/v1/customers", params={"search": "lAn", "platform": "FACEBOOK"})
            assert response.status_code == 200
            lan = response.json()["data"][0]
            assert lan["name"] == "[Demo] Lan"
            customer_path = "/api/v1/customers/" + lan["id"]
            profile = (await client.get(customer_path)).json()["data"]
            assert len(profile["conversation_ids"]) == 4
            assert profile["order_ids"] == []
            assert (await client.post(customer_path + "/notes", json={"content": "  "})).status_code == 422
            note = await client.post(customer_path + "/notes", json={"content": "  Gọi lại chiều nay  "})
            assert note.status_code == 201
            note_id = note.json()["data"]["id"]
            await seed()
            profile = (await client.get(customer_path)).json()["data"]
            assert {entry["content"] for entry in profile["notes"]} >= {"Gọi lại chiều nay"}
            assert len(profile["notes"]) == 2
            assert (await client.get("/api/v1/customers")).json()["meta"]["total"] == 3
            assert (await client.delete(customer_path + "/notes/" + note_id)).status_code == 204
            assert all(entry["id"] != note_id for entry in (await client.get(customer_path)).json()["data"]["notes"])

            root = "/api/v1/conversations"
            first = (await client.get(root, params={"limit": 1, "platform": "FACEBOOK", "status": "NEW"})).json()
            second = (await client.get(root, params={"limit": 1, "page": 2, "platform": "FACEBOOK", "status": "NEW"})).json()
            assert first["meta"] == {"page": 1, "limit": 1, "total": 4}
            conversation = first["data"][0]
            assert conversation["last_message_at"] >= second["data"][0]["last_message_at"]
            assert conversation["id"] != second["data"][0]["id"]
            path = root + "/" + conversation["id"]
            assert (await client.get(path)).json()["data"]["is_read"] is False
            messages = (await client.get(path + "/messages", params={"page": 2})).json()
            assert messages["meta"]["total"] == 22 and len(messages["data"]) == 2
            assert messages["data"][0]["created_at"] < messages["data"][1]["created_at"]
            assert (await client.patch(path + "/read", json={"is_read": 1})).status_code == 422
            read = (await client.patch(path + "/read", json={"is_read": True})).json()["data"]
            assert read["is_read"] is True and read["ai_status"] == conversation["ai_status"]
            assert (await client.patch(path + "/read", json={"is_read": True})).json()["data"]["version"] == read["version"]
            assert (await client.patch(path + "/ai-status", json={
                "ai_status": "SELLER_HANDLING", "expected_version": conversation["version"],
            })).status_code == 409
            takeover = (await client.patch(path + "/ai-status", json={
                "ai_status": "SELLER_HANDLING", "expected_version": read["version"],
            })).json()["data"]
            assert takeover["ai_status"] == "SELLER_HANDLING" and takeover["status"] == "NEW"
            changed = (await client.patch(path + "/status", json={
                "status": "RESOLVED", "expected_version": takeover["version"],
            })).json()["data"]
            assert changed["status"] == "RESOLVED" and changed["ai_status"] == "SELLER_HANDLING"
            async with factory() as db:
                row = await db.scalar(select(Conversation).where(Conversation.id == conversation["id"]))
                assert row.ai_generation == 1 and row.is_read and row.status == "RESOLVED"
            assert (await client.get(root, params={"limit": 101})).status_code == 422
            assert (await client.get(root + "/" + str(uuid4()) + "/messages")).status_code == 404

        async with original_client(transport=httpx.ASGITransport(app=customer.app), base_url="http://customer") as client:
            path = "/internal/customers/upsert"
            body = {"platform": "FACEBOOK", "platform_account_id": "test-page", "platform_user_id": str(uuid4())}
            assert (await client.post(path, json=body, headers=headers)).status_code == 403
            client.headers["Authorization"] = "Bearer local-test-service-token"
            responses = await asyncio.gather(*(client.post(path, json=body) for _ in range(2)))
            rows = [response.json()["data"] for response in responses]
            assert sorted(row["created"] for row in rows) == [False, True]
            assert rows[0]["customer"]["id"] == rows[1]["customer"]["id"]
            zalo = (await client.post(path, json={**body, "platform": "ZALO"})).json()["data"]
            assert zalo["created"] and zalo["customer"]["id"] != rows[0]["customer"]["id"]
    finally:
        for service in (customer, inbox):
            service.app.dependency_overrides.clear()
        await redis.delete(session_key(sid))
        await redis.aclose()
        await engine.dispose()
