"""RT unit/transport checks; fakeredis/SQLite do not prove MySQL row locking."""
import asyncio
import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock
from uuid import uuid4

import fakeredis.aioredis
import jwt
import pytest
import socketio
import uvicorn
from pydantic import ValidationError
from redis.exceptions import ConnectionError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from shared.auth import AuthError, Sessions, issue_access, session_key
from shared.db.models import RealtimeOutbox
from shared.realtime import CHANNEL, Event, dispatch_one, envelope
from tests.conftest import load_service
from tests.test_auth import rsa_keys  # noqa: F401


@pytest.mark.asyncio
async def test_passive_socket_checks_do_not_keep_idle_session_alive(rsa_keys, monkeypatch):
    from shared import auth
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    uid, sid = str(uuid4()), str(uuid4())
    clock = auth.now()
    await Sessions(redis).create(uid, sid)
    token = issue_access(uid, sid)
    monkeypatch.setattr(auth, "now", lambda: clock + 10)
    await Sessions(redis).authorize("Bearer " + token, touch=False)
    assert int(await redis.hget(session_key(sid), "last_seen")) == clock
    await Sessions(redis).authorize("Bearer " + token)
    assert int(await redis.hget(session_key(sid), "last_seen")) == clock + 10
    await redis.hset(session_key(sid), "last_seen", clock - 86400)
    with pytest.raises(AuthError):
        await Sessions(redis).authorize("Bearer " + token, touch=False)
    await redis.aclose()


@pytest.mark.parametrize("name,data", [
    ("conversation:updated", {"conversation_id": "bad", "version": 1}),
    ("conversation:updated", {"conversation_id": str(uuid4()), "version": True}),
    ("realtime:resync", {"token": "must-never-be-forwarded"}),
    ("dashboard:stats:updated", {"changed_at": 1}),
    ("message:updated", {"conversation_id": str(uuid4()), "message_id": str(uuid4()), "status": "BAD"}),
])
def test_invalid_events_are_rejected(name, data):
    with pytest.raises(ValidationError):
        envelope(name, data)


@pytest.mark.asyncio
async def test_outbox_commit_rollback_retry_and_redelivery(tmp_path):
    # Only this independent table is created in an isolated SQLite unit fixture.
    engine = create_async_engine("sqlite+aiosqlite:///" + str(tmp_path / "outbox.db"))
    async with engine.begin() as conn:
        await conn.run_sync(RealtimeOutbox.__table__.create)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    conversation_id = str(uuid4())
    try:
        async with factory() as db:
            db.add(RealtimeOutbox(event_type="conversation:updated", data={"conversation_id": conversation_id, "version": 1}))
            await db.flush()
            # Another connection cannot see uncommitted events.
            assert await dispatch_one(factory, redis) is False
            await db.rollback()
        assert await dispatch_one(factory, redis) is False
        async with factory() as db:
            row = RealtimeOutbox(event_type="conversation:updated", data={"conversation_id": conversation_id, "version": 2})
            db.add(row)
            await db.commit()
            event_id = row.id
        broken = AsyncMock()
        broken.publish.side_effect = ConnectionError("simulated outage")
        assert not await dispatch_one(factory, broken)
        async with factory() as db:
            row = await db.get(RealtimeOutbox, event_id)
            assert row.sent_at is None and row.attempt_count == 1 and row.next_attempt_at is not None
            assert not await dispatch_one(factory, redis)
            row.next_attempt_at = None  # Advance the persisted retry schedule for this test.
            await db.commit()
        async with redis.pubsub() as sub:
            await sub.subscribe(CHANNEL)
            await sub.get_message(timeout=1)  # subscription ack
            assert await dispatch_one(factory, redis)
            message = await sub.get_message(ignore_subscribe_messages=True, timeout=1)
            event = Event.model_validate_json(message["data"])
            assert str(event.event_id) == event_id and event.data["version"] == 2
            assert not await dispatch_one(factory, redis)
            # Simulate acceptance followed by a crash before the sent marker commits.
            async with factory() as db:
                row = await db.get(RealtimeOutbox, event_id)
                row.sent_at = None
                await db.commit()
            assert await dispatch_one(factory, redis)
            again = await sub.get_message(ignore_subscribe_messages=True, timeout=1)
            assert Event.model_validate_json(again["data"]).event_id == event.event_id
        async with factory() as db:
            assert (await db.scalar(select(RealtimeOutbox))).sent_at is not None
    finally:
        await redis.aclose()
        await engine.dispose()


@pytest.mark.asyncio
async def test_socket_transport_auth_events_revocation_and_expiry(rsa_keys, monkeypatch):
    """Real TCP Socket.IO; Redis/session state is explicitly simulated."""
    import socket
    from shared import auth
    module = load_service("realtime-service")
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(module, "redis", redis)
    monkeypatch.setattr(module.sio.eio, "ping_interval", 0.1)
    monkeypatch.setattr(module.sio.eio, "ping_timeout", 0.5)
    module.tokens.clear()

    @asynccontextmanager
    async def lifespan(_app):
        tasks = [asyncio.create_task(module.subscriber()), asyncio.create_task(module.guard_sessions())]
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await module.sio.shutdown()
            await asyncio.sleep(0.2)

    monkeypatch.setattr(module.http_app.router, "lifespan_context", lifespan)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(module.app, log_level="error", lifespan="on"))
    task = asyncio.create_task(server.serve(sockets=[listener]))
    client, rejected = socketio.AsyncClient(), socketio.AsyncClient()
    failures = []
    rejected.on("connect_error", lambda error: failures.append(error))
    uid, sid = str(uuid4()), str(uuid4())
    _, cookie, _ = await Sessions(redis).create(uid, sid)
    token = issue_access(uid, sid)
    received, closed = asyncio.Event(), asyncio.Event()
    payloads = []

    @client.on("conversation:updated")
    async def updated(data):
        payloads.append(data)
        received.set()

    @client.event
    async def disconnect():
        closed.set()

    try:
        async with asyncio.timeout(5):
            while not server.started:
                await asyncio.sleep(0.01)
        root = f"http://127.0.0.1:{port}"
        with pytest.raises(socketio.exceptions.ConnectionError):
            await rejected.connect(root, auth={"token": "invalid"}, transports=["websocket"])
        assert failures[-1] == {"message": "Authentication failed", "data": {"code": "UNAUTHORIZED"}}
        await client.connect(root, auth={"token": token}, transports=["websocket"])
        assert await client.call("conversation:join", {"conversation_id": "bad"}) == {
            "success": False, "error": {"code": "VALIDATION_ERROR"}}
        row = envelope("conversation:updated", {"conversation_id": str(uuid4()), "version": 3})
        await redis.publish(CHANNEL, json.dumps(row))
        await asyncio.wait_for(received.wait(), 3)
        assert payloads == [row]
        await Sessions(redis).logout(cookie, "Bearer " + token)
        await asyncio.wait_for(closed.wait(), 3)
        assert not client.connected
        with pytest.raises(socketio.exceptions.ConnectionError):
            await rejected.connect(root, auth={"token": token}, transports=["websocket"])

        # An access token expiring on an otherwise valid session closes the socket.
        await Sessions(redis).create(uid, sid)
        token = issue_access(uid, sid)
        closed.clear()
        await client.connect(root, auth={"token": token}, transports=["websocket"])
        # A genuine RS256 token with a short remaining lifetime, no decoder stub.
        await client.disconnect()
        closed.clear()
        stamp = auth.now()
        expiring = jwt.encode({**auth.decode_access(token), "iat": stamp - 898, "exp": stamp + 2},
                              rsa_keys[0].read_bytes(), algorithm="RS256")
        await client.connect(root, auth={"token": expiring}, transports=["websocket"])
        await asyncio.wait_for(closed.wait(), 5)
        async with asyncio.timeout(3):
            while client.eio.state != "disconnected":
                await asyncio.sleep(0.01)
        closed.clear()
        await client.connect(root, auth={"token": token}, transports=["websocket"])
        monkeypatch.setattr(redis, "eval", AsyncMock(side_effect=ConnectionError("simulated Redis outage")))
        await asyncio.wait_for(closed.wait(), 3)
    finally:
        await client.disconnect()
        await rejected.disconnect()
        server.should_exit = True
        await asyncio.wait_for(task, 5)
        listener.close()
        module.tokens.clear()
        await redis.aclose()
