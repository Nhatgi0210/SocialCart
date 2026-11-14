"""Catalog through Gateway with isolated MySQL/Redis and temporary image storage."""
import asyncio
from io import BytesIO
import os
import sys
from uuid import uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from PIL import Image
from redis.asyncio import Redis
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from shared.auth import Sessions, issue_access, session_key
from shared.config import settings
from shared.db.models import Customer, Order, OrderItem, Product, Variant
from shared.db.session import get_session
from tests.conftest import BACKEND, load_service
from tests.test_auth import rsa_keys  # noqa: F401


@pytest.mark.asyncio
async def test_product_catalog_through_gateway(monkeypatch, rsa_keys, tmp_path):
    url, cache = os.getenv("SC_TEST_DATABASE_URL"), os.getenv("SC_TEST_REDIS_URL")
    if not url or not cache:
        pytest.skip("Requires isolated MySQL and Redis")
    assert (make_url(url).database or "").startswith("socialcart_test_")
    assert make_url(cache).database == "15"
    monkeypatch.setattr(settings, "database_url", url)
    monkeypatch.setattr(settings, "internal_service_token", "local-test-catalog-token")
    images = tmp_path / "images"
    monkeypatch.setattr(settings, "product_image_dir", str(images))
    monkeypatch.setattr(settings, "product_image_public_base_url", "http://localhost:8000/api/v1/products/images")
    await asyncio.to_thread(command.upgrade, Config(str(BACKEND / "shared/db/alembic.ini")), "head")
    redis = Redis.from_url(cache, decode_responses=True)
    engine = create_async_engine(url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def db_session():
        async with factory() as session:
            yield session

    monkeypatch.setattr(Redis, "from_url", lambda *_args, **_kwargs: redis)
    monkeypatch.syspath_prepend(str(BACKEND / "product-service"))
    old_modules = {name: module for name, module in sys.modules.items() if name == "app" or name.startswith("app.")}
    product_service = load_service("product-service")
    gateway = load_service("api-gateway")
    monkeypatch.setattr(gateway, "get_redis", lambda: redis)
    product_service.app.dependency_overrides[get_session] = db_session
    original_client = httpx.AsyncClient
    monkeypatch.setattr(gateway.httpx, "AsyncClient", lambda **kwargs:
                        original_client(transport=httpx.ASGITransport(app=product_service.app), **kwargs))
    uid, sid = str(uuid4()), str(uuid4())
    await Sessions(redis).create(uid, sid)
    headers = {"Authorization": "Bearer " + issue_access(uid, sid)}
    root = "/api/v1/products"
    image_path = root + "/images"
    try:
        async with original_client(transport=httpx.ASGITransport(app=gateway.app), base_url="http://localhost:8000") as client:
            assert (await client.get(root)).status_code == 401
            assert (await client.post(image_path, files={"file": ("x.png", b"x", "image/png")})).status_code == 401
            assert (await client.get("/internal/catalog", headers=headers)).status_code == 404
            client.headers.update(headers)
            assert (await client.post(image_path, files={"file": ("fake.png", b"<svg></svg>", "image/png")})).status_code == 422
            assert (await client.post(image_path, files={"file": ("large.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")})).status_code == 413
            image = BytesIO()
            Image.new("RGB", (16, 16), "red").save(image, format="PNG")
            assert (await client.post(image_path, files={"file": ("fake.jpg", image.getvalue(), "image/jpeg")})).status_code == 422
            uploaded = await client.post(image_path, files={"file": ("../../image.png", image.getvalue(), "image/png")})
            assert uploaded.status_code == 201
            url_image = uploaded.json()["data"]["image_url"]
            assert url_image.startswith("http://localhost:8000" + image_path + "/")
            assert len(list(images.iterdir())) == 1
            client.headers.pop("Authorization")
            result = await client.get(url_image)
            assert result.status_code == 200 and result.headers["content-type"] == "image/png"
            assert (await client.get(image_path + "/secret.pem")).status_code == 401
            client.headers.update(headers)

            assert (await client.post(root, json={"name": "No variants", "variants": []})).status_code == 422
            data = {"name": "Size M", "price": 150000, "stock": 10, "low_stock_threshold": 2}
            for edits in ({"price": 0}, {"price": 1.5}, {"stock": -1}, {"price": True}):
                assert (await client.post(root, json={"name": "Invalid", "variants": [{**data, **edits}]})).status_code == 422
            assert (await client.post(root, json={"name": "Overflow", "variants": [data, {**data, "stock": 2147483647}]})).status_code == 409
            name = "Áo Catalog QA " + "x" * 185
            created = await client.post(root, json={"name": name, "description": "Demo", "image_url": url_image, "variants": [data]})
            assert created.status_code == 201
            product = created.json()["data"]
            assert product["name"] == name and product["total_stock"] == 10 and product["status"] == "ACTIVE"
            path = root + "/" + product["id"]
            variant = product["variants"][0]
            original_variant = path + "/variants/" + variant["id"]

            async with factory.begin() as db:
                customer = Customer(platform="FACEBOOK", platform_account_id="catalog-test",
                                    platform_user_id=uid, display_name="Catalog test")
                db.add(customer)
                await db.flush()
                order = Order(order_code=f"TEST-{uid}", customer_id=customer.id, total_amount=150000, created_by="SELLER")
                db.add(order)
                await db.flush()
                item = OrderItem(order_id=order.id, variant_id=variant["id"], product_name_snapshot=name,
                                 variant_name_snapshot=variant["name"], unit_price=150000, quantity=1)
                db.add(item)
                await db.flush()
                item_id = item.id

            edit = await client.put(path, json={"name": "Áo Catalog QA updated"})
            assert edit.status_code == 200 and edit.json()["data"]["description"] == "Demo"
            other = await client.post(path + "/variants", json={**data, "name": "Size L", "stock": 3})
            assert other.status_code == 201
            other_variant = path + "/variants/" + other.json()["data"]["id"]
            requests = [client.put(original_variant, json={"expected_version": 1, "price": 175000, "stock": 0}) for _ in range(2)]
            changes = await asyncio.gather(*requests)
            assert sorted(response.status_code for response in changes) == [200, 409]
            detail = (await client.get(path)).json()["data"]
            assert detail["total_stock"] == 3
            saved = next(row for row in detail["variants"] if row["id"] == variant["id"])
            assert saved["price"] == 175000 and saved["stock"] == 0 and saved["version"] == 2
            match = (await client.get(root, params={"search": "CATALOG QA", "status": "ACTIVE", "low_stock": True, "limit": 1})).json()
            assert match["data"][0]["id"] == product["id"] and match["meta"] == {"total": 1, "page": 1, "limit": 1}
            assert (await client.get(root, params={"search": "CATALOG QA", "page": 2, "limit": 1})).json()["data"] == []
            assert (await client.get(root, params={"search": "CATALOG QA", "low_stock": False})).json()["data"] == []

            async with original_client(transport=httpx.ASGITransport(app=product_service.app), base_url="http://product") as internal:
                assert (await internal.get("/internal/catalog", headers=headers)).status_code == 403
                internal.headers["Authorization"] = "Bearer local-test-catalog-token"
                listed = (await internal.get("/internal/catalog")).json()["data"]
                assert product["id"] in {row["id"] for row in listed}
                assert (await client.delete(original_variant)).status_code == 204
                assert (await client.delete(other_variant)).status_code == 204
                closed = (await client.get(path)).json()["data"]
                assert closed["status"] == "INACTIVE" and closed["variants"] == [] and closed["total_stock"] == 0
                assert (await client.put(path, json={"status": "ACTIVE"})).status_code == 409
                listed = (await internal.get("/internal/catalog")).json()["data"]
                assert product["id"] not in {row["id"] for row in listed}

            assert (await client.post(path + "/variants", json=data)).status_code == 201
            assert (await client.put(path, json={"status": "ACTIVE"})).status_code == 200
            assert (await client.delete(path)).status_code == 204
            assert (await client.get(path)).status_code == 404
            assert (await client.get(root, params={"search": "CATALOG QA"})).json()["data"] == []
            async with factory() as db:
                assert (await db.get(Product, product["id"])).deleted_at is not None
                assert (await db.get(Variant, variant["id"])).deleted_at is not None
                snapshot = await db.get(OrderItem, item_id)
                assert snapshot.product_name_snapshot == name and snapshot.unit_price == 150000
    finally:
        product_service.app.dependency_overrides.clear()
        await redis.delete(session_key(sid))
        await redis.aclose()
        await engine.dispose()
        for name in list(sys.modules):
            if (name == "app" or name.startswith("app.")) and name not in old_modules:
                sys.modules.pop(name)
