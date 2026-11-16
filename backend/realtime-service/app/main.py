"""RT-01: authenticated Socket.IO, durable publication and Pub/Sub recovery."""
import asyncio
import logging
from contextlib import asynccontextmanager
from uuid import UUID

import socketio
from fastapi import FastAPI
from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from shared.auth import AuthError, Sessions
from shared.config import settings
from shared.db.models import Conversation
from shared.db.session import db_lifespan, get_session_factory
from shared.health import readiness
from shared.realtime import CHANNEL, Event, dispatch_one, envelope

logger = logging.getLogger(__name__)
redis = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=3, socket_timeout=3)
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=settings.cors_allowed_origins,
                          logger=False, engineio_logger=False)
tokens: dict[str, str] = {}


async def authorized(sid):
    token = tokens.get(sid)
    if token is None:
        return False
    try:
        await Sessions(redis).authorize("Bearer " + token, touch=False)
        return True
    except AuthError:
        await sio.disconnect(sid)
        return False


@sio.event
async def connect(sid, environ, auth):
    if not isinstance(auth, dict) or not isinstance(auth.get("token"), str):
        raise socketio.exceptions.ConnectionRefusedError("Authentication failed", {"code": "UNAUTHORIZED"})
    try:
        claims = await Sessions(redis).authorize("Bearer " + auth["token"])
    except AuthError as exc:
        raise socketio.exceptions.ConnectionRefusedError("Authentication failed", {"code": exc.code}) from None
    tokens[sid] = auth["token"]
    await sio.enter_room(sid, "seller:" + claims["sub"])


@sio.event
async def disconnect(sid):
    tokens.pop(sid, None)


@sio.on("conversation:join")
async def join_conversation(sid, data):
    if not await authorized(sid):
        return {"success": False, "error": {"code": "UNAUTHORIZED"}}
    try:
        if not isinstance(data, dict) or set(data) != {"conversation_id"}:
            raise ValueError
        id = str(UUID(data["conversation_id"]))
        if id != data["conversation_id"]:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        return {"success": False, "error": {"code": "VALIDATION_ERROR"}}
    try:
        async with get_session_factory()() as db:
            exists = await db.scalar(select(Conversation.id).where(Conversation.id == id))
    except SQLAlchemyError:
        return {"success": False, "error": {"code": "SERVICE_UNAVAILABLE"}}
    if not exists:
        return {"success": False, "error": {"code": "NOT_FOUND"}}
    await sio.enter_room(sid, "conversation:" + id)
    return {"success": True}


async def broadcast(event):
    # Check every recipient at send time, including revoked/expired sessions.
    for sid in list(tokens):
        if await authorized(sid):
            await sio.emit(event["event_type"], event, to=sid)


async def subscriber():
    while True:
        try:
            async with redis.pubsub() as pubsub:
                await pubsub.subscribe(CHANNEL)
                async for message in pubsub.listen():
                    if message["type"] == "subscribe":
                        # Also covers a Redis reconnect while sockets stayed open.
                        await broadcast(envelope("realtime:resync", {}))
                    elif message["type"] == "message":
                        try:
                            event = Event.model_validate_json(message["data"]).model_dump(mode="json")
                        except (ValidationError, ValueError, TypeError):
                            logger.warning("Ignored invalid realtime event")
                            continue
                        await broadcast(event)
        except (RedisError, OSError):
            logger.warning("Realtime subscription unavailable; retrying")
            await asyncio.sleep(1)


async def publisher():
    while True:
        try:
            if await dispatch_one(get_session_factory(), redis):
                continue
        except (RedisError, SQLAlchemyError):
            logger.warning("Realtime publication unavailable; outbox retained")
        await asyncio.sleep(1)


async def guard_sessions():
    while True:
        await asyncio.sleep(1)
        for sid in list(tokens):
            await authorized(sid)


@asynccontextmanager
async def lifespan(_app):
    async with db_lifespan():
        tasks = [asyncio.create_task(run()) for run in (subscriber, publisher, guard_sessions)]
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            for sid in list(tokens):
                await sio.disconnect(sid)
            await sio.shutdown()
            await redis.aclose()


http_app = FastAPI(title="SocialCart Realtime Service", lifespan=lifespan)


@http_app.get("/health")
async def health():
    return await readiness("realtime-service", redis)


app = socketio.ASGIApp(sio, http_app)
