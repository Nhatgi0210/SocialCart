"""MySQL commit/row-lock and real Redis publish checks on opt-in isolated infra."""
import asyncio
import importlib.util
import json
import os
import socket
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
import httpx
import socketio
import uvicorn
from alembic import command
from alembic.config import Config
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from shared.config import settings
from shared.auth import Sessions, issue_access, session_key
from shared.db.models import Conversation, Customer, RealtimeOutbox
from shared.db.session import get_session
from shared.realtime import CHANNEL, Event, dispatch_one, envelope
from tests.conftest import BACKEND
from tests.test_auth import rsa_keys  # noqa: F401


@pytest.mark.asyncio
async def test_mysql_outbox_commit_and_concurrent_publishers(monkeypatch):
    url, cache = os.getenv("SC_TEST_DATABASE_URL"), os.getenv("SC_TEST_REDIS_URL")
    if not url or not cache:
        pytest.skip("Requires isolated MySQL/Redis")
    assert (make_url(url).database or "").startswith("socialcart_test_")
    assert make_url(cache).database == "15"
    monkeypatch.setattr(settings, "database_url", url)
    await asyncio.to_thread(command.upgrade, Config(str(BACKEND / "shared/db/alembic.ini")), "head")
    engine = create_async_engine(url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = Redis.from_url(cache, decode_responses=True)
    broken = Redis.from_url("redis://127.0.0.1:1/15", socket_connect_timeout=0.2, socket_timeout=0.2)
    try:
        # Previous API integration checks can have left committed pending events.
        while await dispatch_one(factory, redis):
            pass
        async with factory() as db:
            db.add(RealtimeOutbox(event_type="conversation:updated", data={"conversation_id": str(uuid4()), "version": 1}))
            await db.flush()
            assert not await dispatch_one(factory, redis)
            await db.rollback()
        async with factory() as db:
            row = RealtimeOutbox(event_type="conversation:updated", data={"conversation_id": str(uuid4()), "version": 2})
            db.add(row)
            await db.commit()
            event_id = row.id
        assert not await dispatch_one(factory, broken)
        async with factory() as db:
            row = await db.get(RealtimeOutbox, event_id)
            assert row.sent_at is None and row.attempt_count == 1 and row.next_attempt_at is not None
            assert not await dispatch_one(factory, redis)
            row.next_attempt_at = None
            await db.commit()
        async with redis.pubsub() as sub:
            await sub.subscribe(CHANNEL)
            await sub.get_message(timeout=1)
            results = await asyncio.gather(dispatch_one(factory, redis), dispatch_one(factory, redis))
            assert sorted(results) == [False, True]
            message = await sub.get_message(ignore_subscribe_messages=True, timeout=2)
            event = Event.model_validate_json(message["data"])
            assert str(event.event_id) == event_id and event.data["version"] == 2
            assert await sub.get_message(ignore_subscribe_messages=True, timeout=0.2) is None
        async with factory() as db:
            assert (await db.scalar(select(RealtimeOutbox).where(RealtimeOutbox.id == event_id))).sent_at is not None
    finally:
        await broken.aclose()
        await redis.aclose()
        await engine.dispose()


@pytest.mark.asyncio
async def test_real_inbox_mutation_to_tcp_socket_and_pubsub_recovery(monkeypatch, rsa_keys):
    url, cache = os.getenv("SC_TEST_DATABASE_URL"), os.getenv("SC_TEST_REDIS_URL")
    if not url or not cache:
        pytest.skip("Requires isolated MySQL/Redis")
    assert (make_url(url).database or "").startswith("socialcart_test_")
    assert make_url(cache).database == "15"
    monkeypatch.setattr(settings, "database_url", url)
    monkeypatch.setattr(settings, "redis_url", cache)
    await asyncio.to_thread(command.upgrade, Config(str(BACKEND / "shared/db/alembic.ini")), "head")
    engine = create_async_engine(url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = Redis.from_url(cache, decode_responses=True)
    # Fresh Socket.IO runtime, independent of the fakeredis TCP unit fixture.
    spec = importlib.util.spec_from_file_location("realtime_integration_main", BACKEND / "realtime-service/app/main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "get_session_factory", lambda: factory)
    monkeypatch.setattr(module.sio.eio, "ping_interval", 0.1)
    monkeypatch.setattr(module.sio.eio, "ping_timeout", 0.5)

    @asynccontextmanager
    async def database_lifespan():
        yield  # The test owns and disposes the real MySQL pool below.

    monkeypatch.setattr(module, "db_lifespan", database_lifespan)
    inbox_spec = importlib.util.spec_from_file_location("realtime_inbox_main", BACKEND / "conversation-service/app/main.py")
    inbox = importlib.util.module_from_spec(inbox_spec)
    inbox_spec.loader.exec_module(inbox)
    async def db_session():
        async with factory() as db:
            yield db
    inbox.app.dependency_overrides[get_session] = db_session

    uid, sid = str(uuid4()), str(uuid4())
    _, cookie, _ = await Sessions(redis).create(uid, sid)
    token = issue_access(uid, sid)
    async with factory() as db:
        customer = Customer(id=str(uuid4()), platform="FACEBOOK", platform_account_id="rt-test-page",
                            platform_user_id=str(uuid4()), display_name="Realtime test")
        db.add(customer)
        await db.flush()
        conversation = Conversation(id=str(uuid4()), platform="FACEBOOK", platform_account_id="rt-test-page",
                                    platform_chat_id=str(uuid4()), customer_id=customer.id,
                                    status="NEW", ai_status="AI_HANDLING", is_read=False, version=1)
        db.add(conversation)
        await db.commit()
        id, version, target = conversation.id, 1, "IN_PROGRESS"
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    root = f"http://127.0.0.1:{listener.getsockname()[1]}"
    server = uvicorn.Server(uvicorn.Config(module.app, log_level="error", lifespan="on"))
    task = asyncio.create_task(server.serve(sockets=[listener]))
    client = socketio.AsyncClient()
    events, resyncs, closed = asyncio.Queue(), asyncio.Queue(), asyncio.Event()
    client.on("conversation:updated", lambda event: events.put_nowait(event))
    client.on("realtime:resync", lambda event: resyncs.put_nowait(event))
    client.on("disconnect", lambda: closed.set())
    try:
        async with asyncio.timeout(5):
            while not server.started:
                await asyncio.sleep(0.01)
        await client.connect(root, auth={"token": token}, transports=["websocket"])
        assert await client.call("conversation:join", {"conversation_id": id}) == {"success": True}
        assert (await client.call("conversation:join", {"conversation_id": str(uuid4())}))["error"]["code"] == "NOT_FOUND"
        async with inbox.app.router.lifespan_context(inbox.app), httpx.AsyncClient(
            transport=httpx.ASGITransport(app=inbox.app), base_url="http://inbox",
            headers={"Authorization": "Bearer " + token},
        ) as http:
            response = await http.patch(f"/api/v1/conversations/{id}/status", json={"status": target, "expected_version": version})
            assert response.status_code == 200
        async with asyncio.timeout(5):
            while True:
                event = await events.get()
                if event["data"] == {"conversation_id": id, "version": version + 1}:
                    break
        # Kill only this service's subscriber connection; sockets remain connected.
        async with asyncio.timeout(5):
            while True:
                subscriptions = [entry for entry in await redis.client_list() if "P" in entry["flags"] and entry["db"] == "15"]
                if subscriptions:
                    break
                await asyncio.sleep(0.01)
        while not resyncs.empty():
            resyncs.get_nowait()
        await redis.client_kill_filter(_id=subscriptions[0]["id"])
        recovered = await asyncio.wait_for(resyncs.get(), 5)
        assert recovered["event_type"] == "realtime:resync" and client.connected
        # Events still reach the same socket after the Redis subscription recovers.
        expected = envelope("conversation:updated", {"conversation_id": id, "version": version + 2})
        await redis.publish(CHANNEL, json.dumps(expected))
        assert (await asyncio.wait_for(events.get(), 3))["event_id"] == expected["event_id"]
        await Sessions(redis).logout(cookie, "Bearer " + token)
        await asyncio.wait_for(closed.wait(), 3)
        assert not client.connected
    finally:
        inbox.app.dependency_overrides.clear()
        await client.disconnect()
        server.should_exit = True
        await asyncio.wait_for(task, 5)
        await asyncio.sleep(0.2)
        listener.close()
        await redis.delete(session_key(sid))
        await redis.aclose()
        await engine.dispose()
