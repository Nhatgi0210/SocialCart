"""Opt-in MySQL/Redis integration; never uses the application's DATABASE_URL.

SC_TEST_DATABASE_URL must target a database named socialcart_test_*;
SC_TEST_REDIS_URL must select DB 15. Migrations persist; only this test's rows
and session keys are removed. No DROP DATABASE, FLUSHDB or volume deletion.
"""
import asyncio
import os
from uuid import uuid4

import httpx
import pytest
import redis.asyncio as aioredis
from alembic import command
from alembic.config import Config
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tests.conftest import BACKEND, load_service
from tests.test_auth import ORIGIN, PASSWORD, rsa_keys  # noqa: F401 — shared pytest fixture
from shared import auth as security
from shared.config import settings
from shared.db.models import User
from shared.db.session import get_session
from shared.passwords import hash_password


@pytest.mark.asyncio
async def test_mysql_redis_gateway_auth(monkeypatch, rsa_keys):
    db_url, redis_url = os.getenv("SC_TEST_DATABASE_URL"), os.getenv("SC_TEST_REDIS_URL")
    if not db_url or not redis_url:
        pytest.skip("Set SC_TEST_DATABASE_URL and SC_TEST_REDIS_URL for isolated MySQL/Redis integration")
    database, cache = make_url(db_url), make_url(redis_url)
    assert database.drivername == "mysql+aiomysql" and (database.database or "").startswith("socialcart_test_")
    assert cache.drivername in {"redis", "rediss"} and cache.database == "15"
    monkeypatch.setattr(settings, "database_url", db_url)
    # Alembic's async runner owns a separate event loop in the worker thread.
    config = Config(str(BACKEND / "shared/db/alembic.ini"))
    await asyncio.to_thread(command.upgrade, config, "head")
    engine = create_async_engine(db_url, echo=False, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = aioredis.from_url(redis_url, decode_responses=True, socket_timeout=3, socket_connect_timeout=3)
    uid = str(uuid4())
    user = User(id=uid, email=f"{uid}@example.com", name="Integration seller",
                hashed_password=hash_password(PASSWORD), is_active=True)
    auth, gateway = load_service("auth-service"), load_service("api-gateway")
    monkeypatch.setattr(auth, "get_redis", lambda: redis)
    monkeypatch.setattr(gateway, "get_redis", lambda: redis)

    async def database_session():
        async with factory() as session:
            yield session

    auth.app.dependency_overrides[get_session] = database_session
    original_client = httpx.AsyncClient
    monkeypatch.setattr(gateway.httpx, "AsyncClient", lambda **kwargs:
                        original_client(transport=httpx.ASGITransport(app=auth.app), **kwargs))
    try:
        await redis.ping()
        async with factory() as session:
            session.add(user)
            await session.commit()
        async with original_client(transport=httpx.ASGITransport(app=gateway.app), base_url="http://localhost:8000") as client:
            response = await client.post("/api/v1/auth/login", headers=ORIGIN,
                                         json={"email": user.email, "password": PASSWORD})
            assert response.status_code == 200
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": "Bearer " + token}
            assert (await client.get("/api/v1/auth/me", headers=headers)).json()["data"]["id"] == uid
            cookie = client.cookies.get("sc_refresh")
            responses = await asyncio.gather(*[client.post("/api/v1/auth/refresh", headers={
                **ORIGIN, "Cookie": "sc_refresh=" + cookie}) for _ in range(2)])
            assert sorted(r.status_code for r in responses) == [200, 401]
            assert (await client.post("/api/v1/auth/logout", headers={**ORIGIN, **headers})).status_code == 204
            assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401
            await redis.delete(f"sc:blacklist:{security.decode_access(token)['jti']}")
    finally:
        auth.app.dependency_overrides.clear()
        # Remove only session records owned by this uniquely generated seller.
        async for key in redis.scan_iter("sc:session:*"):
            if await redis.hget(key, "uid") == uid:
                await redis.delete(key)
        async with factory() as session:
            await session.execute(delete(User).where(User.id == uid))
            await session.commit()
        await redis.aclose()
        await engine.dispose()
