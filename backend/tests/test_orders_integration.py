"""Exercise real MySQL stock locks and idempotency through Gateway."""
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
from shared.db.models import Conversation, Customer, InventoryMovement, Product, RealtimeOutbox, Variant
from shared.db.session import get_session
from tests.conftest import BACKEND, load_service
from tests.test_auth import rsa_keys  # noqa: F401


@pytest.mark.asyncio
async def test_order_lifecycle_and_competing_stock(monkeypatch, rsa_keys):
    database, cache = os.getenv("SC_TEST_DATABASE_URL"), os.getenv("SC_TEST_REDIS_URL")
    if not database or not cache:
        pytest.skip("Requires isolated MySQL and Redis")
    assert (make_url(database).database or "").startswith("socialcart_test_")
    assert make_url(cache).database == "15"
    monkeypatch.setattr(settings, "database_url", database)
    await asyncio.to_thread(command.upgrade, Config(str(BACKEND / "shared/db/alembic.ini")), "head")
    engine = create_async_engine(database, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = Redis.from_url(cache, decode_responses=True)
    actor, sid = str(uuid4()), str(uuid4())
    await Sessions(redis).create(actor, sid)

    async def db_session():
        async with factory() as db:
            yield db

    monkeypatch.setattr(Redis, "from_url", lambda *_args, **_kwargs: redis)
    monkeypatch.syspath_prepend(str(BACKEND / "order-service"))
    previous = {name: module for name, module in sys.modules.items() if name == "app" or name.startswith("app.")}
    service = load_service("order-service")
    gateway = load_service("api-gateway")
    service.app.dependency_overrides[get_session] = db_session
    monkeypatch.setattr(gateway, "get_redis", lambda: redis)
    http_client = httpx.AsyncClient
    monkeypatch.setattr(gateway.httpx, "AsyncClient", lambda **kwargs:
                        http_client(transport=httpx.ASGITransport(app=service.app), **kwargs))
    root = "/api/v1/orders"

    try:
        async with factory.begin() as db:
            customer = Customer(platform="FACEBOOK", platform_account_id="orders-test", platform_user_id=actor)
            product = Product(name="Áo gốc", status="ACTIVE")
            db.add_all([product, customer])
            await db.flush()
            conversation = Conversation(platform="FACEBOOK", platform_account_id="orders-test", customer_id=customer.id,
                                        platform_chat_id=actor)
            first = Variant(product_id=product.id, name="Size M", price=100000, stock=1)
            second = Variant(product_id=product.id, name="Size L", price=120000, stock=2)
            db.add_all([conversation, first, second])

        async def stock():
            async with factory() as db:
                return (await db.get(Variant, first.id)).stock, (await db.get(Variant, second.id)).stock

        def item(variant):
            return {"variant_id": variant.id, "quantity": 1}

        async with http_client(transport=httpx.ASGITransport(app=gateway.app), base_url="http://gateway") as client:
            assert (await client.get(root)).status_code == 401
            client.headers["Authorization"] = "Bearer " + issue_access(actor, sid)
            payload = {"customer_id": customer.id, "conversation_id": conversation.id,
                       "customer_name": "Khách demo", "phone_number": "0900000000", "address": "Địa chỉ test",
                       "items": [item(first)]}

            async def create(body=payload, key=None):
                return await client.post(root, json=body, headers={"Idempotency-Key": key or str(uuid4())})

            async def patch(order, body, suffix="", key=None):
                return await client.patch(root + "/" + order["id"] + suffix, json=body,
                                          headers={"Idempotency-Key": key or str(uuid4())})

            async def status(order, target, key=None):
                return await patch(order, {"status": target, "expected_version": order["version"]}, "/status", key)

            assert (await create({**payload, "customer_id": str(uuid4())})).status_code == 422
            assert (await create({**payload, "items": [item(first), item(first)]})).json()["error"]["code"] == "INSUFFICIENT_STOCK"
            assert (await create({**payload, "items": [{**item(first), "unit_price": 1}]})).status_code == 422
            key = str(uuid4())
            creates = await asyncio.gather(create(key=key), create(key=key))
            assert [result.status_code for result in creates] == [201, 201], [result.text for result in creates]
            one = creates[0].json()["data"]
            assert creates[0].json() == creates[1].json()
            assert (await create({**payload, "note": "different"}, key)).json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
            assert await stock() == (1, 2)

            async with factory.begin() as db:
                (await db.get(Product, product.id)).name = "Áo mới"
                variant = await db.get(Variant, first.id)
                variant.name, variant.price = "M mới", 150000
            updated = await patch(one, {"expected_version": one["version"], "items": [item(first), item(second)]})
            assert updated.status_code == 200, updated.text
            one = updated.json()["data"]
            lines = {row["variant_id"]: row for row in one["items"]}
            assert (lines[first.id]["product_name"], lines[first.id]["variant_name"], lines[first.id]["unit_price"]) == (
                "Áo gốc", "Size M", 100000)
            assert lines[second.id]["product_name"] == "Áo mới" and one["total_amount"] == 220000
            # Both pending orders use the same final piece, plus a variant unique to one order.
            two = (await create()).json()["data"]
            assert two["total_amount"] == 150000 and await stock() == (1, 2)
            listing = await client.get(root, params={"status": "PENDING", "conversation_id": conversation.id, "limit": 1})
            assert listing.json()["meta"]["total"] == 2 and len(listing.json()["data"]) == 1
            keys = [str(uuid4()), str(uuid4())]
            confirms = await asyncio.gather(status(one, "CONFIRMED", keys[0]), status(two, "CONFIRMED", keys[1]))
            assert sorted(result.status_code for result in confirms) == [200, 409], [result.text for result in confirms]
            winner = next(index for index, result in enumerate(confirms) if result.status_code == 200)
            loser = 1 - winner
            assert confirms[loser].json()["error"]["code"] == "INSUFFICIENT_STOCK"
            assert await stock() == (0, 1 if winner == 0 else 2)
            original = [one, two]
            confirmed = confirms[winner].json()["data"]
            assert (await status(original[winner], "CONFIRMED", keys[winner])).json()["data"] == confirmed
            assert (await status(original[winner], "CONFIRMED")).json()["error"]["code"] == "VERSION_CONFLICT"
            assert (await patch(confirmed, {"expected_version": confirmed["version"], "note": "late"})).status_code == 409
            shipped = (await status(confirmed, "SHIPPING")).json()["data"]

            cancel_key = str(uuid4())
            cancels = await asyncio.gather(status(shipped, "CANCELLED", cancel_key), status(shipped, "CANCELLED", cancel_key))
            assert [result.status_code for result in cancels] == [200, 200]
            assert cancels[0].json() == cancels[1].json()
            assert await stock() == (1, 2)
            assert (await status(cancels[0].json()["data"], "CANCELLED")).json()["error"]["code"] == "INVALID_TRANSITION"

            pending = original[loser]
            assert (await status(pending, "CANCELLED")).status_code == 200
            assert await stock() == (1, 2)
            multi = (await create({**payload, "items": [item(second), item(first)]})).json()["data"]
            fresh = (await create()).json()["data"]
            confirmed_again = (await status(fresh, "CONFIRMED")).json()["data"]
            assert (await status(multi, "CONFIRMED")).json()["error"]["code"] == "INSUFFICIENT_STOCK"
            assert await stock() == (0, 2)
            direct = (await create({**payload, "items": [item(second)]})).json()["data"]
            direct = (await status(direct, "CONFIRMED")).json()["data"]
            async with factory.begin() as db:
                variant = await db.get(Variant, second.id)
                variant.deleted_at = variant.updated_at
            assert (await status(direct, "CANCELLED")).status_code == 200
            assert await stock() == (0, 2)
            shipping_again = (await status(confirmed_again, "SHIPPING")).json()["data"]
            completed = (await status(shipping_again, "COMPLETED")).json()["data"]
            assert completed["status"] == "COMPLETED"
            assert (await status(completed, "CANCELLED")).status_code == 409
            assert await stock() == (0, 2)
            async with factory.begin() as db:
                variant = await db.get(Variant, first.id)
                variant.deleted_at = variant.updated_at
            assert (await client.get(root + "/" + one["id"])).json()["data"]["items"] == one["items"]

            async with factory.begin() as db:
                bulk = Product(name="ệ" * 200, status="ACTIVE")
                db.add(bulk)
                await db.flush()
                bulk_variants = [Variant(product_id=bulk.id, name=f"{index:02d}" + "ệ" * 98, price=1, stock=1)
                                 for index in range(80)]
                db.add_all(bulk_variants)
            large = {**payload, "items": [item(variant) for variant in bulk_variants]}
            large_key = str(uuid4())
            response = await create(large, large_key)
            assert response.status_code == 201 and len(response.content) > 65535
            assert (await create(large, large_key)).json() == response.json()

        async with factory() as db:
            movements = list(await db.scalars(select(InventoryMovement).where(InventoryMovement.order_id == confirmed["id"])))
            assert {(row.variant_id, row.movement_type, row.quantity) for row in movements} == {
                (item["variant_id"], kind, item["quantity"])
                for item in confirmed["items"] for kind in ("DEDUCT", "RESTORE")
            }
            assert not await db.scalar(select(InventoryMovement.id).where(InventoryMovement.order_id == pending["id"]))
            assert not await db.scalar(select(InventoryMovement.id).where(InventoryMovement.order_id == multi["id"]))
            events = list(await db.scalars(select(RealtimeOutbox)))
            assert sum(event.event_type == "order:created" and event.data["order_id"] == one["id"] for event in events) == 1
            assert sum(event.event_type == "order:updated" and event.data["order_id"] == confirmed["id"]
                       and event.data["version"] == cancels[0].json()["data"]["version"] for event in events) == 1
    finally:
        service.app.dependency_overrides.clear()
        for name in tuple(sys.modules):
            if (name == "app" or name.startswith("app.")) and name not in previous:
                sys.modules.pop(name, None)
        await redis.delete(session_key(sid))
        await redis.aclose()
        await engine.dispose()
