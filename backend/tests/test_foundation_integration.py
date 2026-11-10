"""Real MySQL seed/schema and Redis health checks on opt-in isolated infrastructure."""
import importlib.util
import os
from uuid import uuid4

import httpx
import pytest
import redis.asyncio as aioredis
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tests.conftest import BACKEND, load_service
from shared.db.models import Base, User, Product, Variant
from shared.passwords import verify_password


@pytest.mark.asyncio
async def test_real_seed_schema_and_health(monkeypatch):
    raw, cache = os.getenv("SC_TEST_DATABASE_URL"), os.getenv("SC_TEST_REDIS_URL")
    if not raw or not cache:
        pytest.skip("Requires isolated MySQL/Redis URLs")
    url = make_url(raw)
    assert url.drivername == "mysql+aiomysql" and url.database.startswith("socialcart_test_")
    assert make_url(cache).database == "15"
    engine = create_async_engine(raw)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = aioredis.from_url(cache, socket_connect_timeout=1, socket_timeout=1)
    bad_redis = aioredis.from_url("redis://127.0.0.1:1/15", socket_connect_timeout=1, socket_timeout=1)
    bad_engine = create_async_engine(url.set(port=1), connect_args={"connect_timeout": 1})
    try:
        async with engine.begin() as conn:
            def upgrade(sync):
                config = Config(str(BACKEND / "shared/db/alembic.ini"))
                config.attributes["connection"] = sync
                command.upgrade(config, "head")
            await conn.run_sync(upgrade)
        async with engine.connect() as conn:
            def schema(sync):
                actual = inspect(sync)
                assert set(actual.get_table_names()) == set(Base.metadata.tables) | {"alembic_version"}
                for name, table in Base.metadata.tables.items():
                    assert {c["name"] for c in actual.get_columns(name)} == set(table.columns.keys())
                    assert actual.get_table_options(name)["mysql_engine"] == "InnoDB"
                assert "ck_variant_threshold_nonneg" in {c["name"] for c in actual.get_check_constraints("variants")}
            await conn.run_sync(schema)
            assert (await conn.execute(text("SELECT @@session.time_zone"))).scalar() == "+00:00"
        spec = importlib.util.spec_from_file_location("real_seed", BACKEND.parent / "scripts/seed-demo.py")
        seed = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(seed)
        email = f"{uuid4()}@example.test"
        password = " test seed password with spaces "
        monkeypatch.setenv("SEED_SELLER_EMAIL", email)
        monkeypatch.setenv("SEED_SELLER_PASSWORD", password)
        monkeypatch.setenv("SEED_SELLER_NAME", "Local test seller")
        async with factory() as session:
            await seed.seed_seller(session)
            await seed.seed_demo_catalog(session)
            first = (await session.execute(select(User).where(User.email == email))).scalar_one()
            original = (first.id, first.hashed_password, first.name)
            monkeypatch.setenv("SEED_SELLER_PASSWORD", "another password")
            await seed.seed_seller(session)
            await seed.seed_demo_catalog(session)
            await session.refresh(first)
            assert (first.id, first.hashed_password, first.name) == original
            assert verify_password(password, first.hashed_password)
            assert len((await session.execute(select(User).where(User.email == email))).scalars().all()) == 1
            assert len((await session.execute(select(Product))).scalars().all()) == 2
            assert len((await session.execute(select(Variant))).scalars().all()) == 6
            variant = (await session.execute(select(Variant))).scalars().first()
            for assignment in ("stock=-1", "price=0", "version=0", "low_stock_threshold=-1"):
                with pytest.raises(OperationalError) as exc:
                    async with session.begin_nested():
                        await session.execute(text(f"UPDATE variants SET {assignment} WHERE id=:id"), {"id": variant.id})
                assert exc.value.orig.args[0] == 3819  # MySQL CHECK violation
            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    await session.execute(text("UPDATE variants SET product_id=:id WHERE id=:variant"),
                                          {"id": str(uuid4()), "variant": variant.id})
            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    await session.execute(text("INSERT INTO users (id,email,name,hashed_password,is_active,created_at,updated_at) "
                                              "SELECT :id,email,name,hashed_password,is_active,created_at,updated_at FROM users WHERE id=:source"),
                                          {"id": str(uuid4()), "source": first.id})
        import shared.health as health
        for service in ("api-gateway", "auth-service"):
            module = load_service(service)
            for db_ok, redis_ok in ((True, True), (False, True), (True, False)):
                monkeypatch.setattr(health, "get_engine", lambda: engine if db_ok else bad_engine)
                monkeypatch.setattr(module, "get_redis", lambda: redis if redis_ok else bad_redis)
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=module.app), base_url="http://test") as client:
                    response = await client.get("/health")
                assert response.status_code == (200 if db_ok and redis_ok else 503)
                assert "password" not in response.text
        assert (await redis.info("server"))["redis_version"].startswith("7.")
    finally:
        await redis.aclose()
        await bad_redis.aclose()
        await engine.dispose()
        await bad_engine.dispose()
