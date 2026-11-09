"""HTTP + real RSA + Redis Lua under fakeredis; DB repository is simulated.

These tests do not establish MySQL/Redis integration or browser E2E.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import bcrypt
import fakeredis.aioredis
import httpx
import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from redis.exceptions import ConnectionError
from sqlalchemy.exc import OperationalError

from tests.conftest import load_service
from shared import auth as security
from shared.config import settings
from shared.db.session import get_session
from shared.passwords import hash_password, verify_password

ORIGIN = {"Origin": "http://localhost:5173"}
PASSWORD = "local-only-test-password"
HTTP_CLIENT = httpx.AsyncClient


@pytest.fixture
def rsa_keys(tmp_path, monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = tmp_path / "private.pem"
    public = tmp_path / "public.pem"
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                         serialization.NoEncryption()))
    public.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
                                                    serialization.PublicFormat.SubjectPublicKeyInfo))
    monkeypatch.setattr(settings, "jwt_private_key_path", str(private))
    monkeypatch.setattr(settings, "jwt_public_key_path", str(public))
    return private, public


@pytest_asyncio.fixture
async def stack(rsa_keys, monkeypatch):
    auth, gateway = load_service("auth-service"), load_service("api-gateway")
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    user = SimpleNamespace(id=str(uuid4()), email="seller@example.com", name="Chủ shop",
                           hashed_password=hash_password(PASSWORD), is_active=True)
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db.execute.return_value = result
    db.get.return_value = user

    async def database():
        yield db

    auth.app.dependency_overrides[get_session] = database
    monkeypatch.setattr(auth, "get_redis", lambda: redis)
    monkeypatch.setattr(gateway, "get_redis", lambda: redis)
    original_client = HTTP_CLIENT

    # Exercise the actual Gateway proxy through an ASGI upstream; no live server.
    def upstream_client(**kwargs):
        return original_client(transport=httpx.ASGITransport(app=auth.app), **kwargs)

    monkeypatch.setattr(gateway.httpx, "AsyncClient", upstream_client)
    async with original_client(transport=httpx.ASGITransport(app=gateway.app), base_url="http://localhost:8000") as client:
        yield SimpleNamespace(client=client, redis=redis, user=user, db=db, result=result, auth=auth, gateway=gateway)
    auth.app.dependency_overrides.clear()
    await redis.aclose()


async def login(stack):
    return await stack.client.post("/api/v1/auth/login", headers=ORIGIN,
                                   json={"email": stack.user.email, "password": PASSWORD})


@pytest.mark.asyncio
async def test_login_me_refresh_logout_through_gateway(stack):
    response = await login(stack)
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["user"] == {"id": stack.user.id, "email": stack.user.email, "name": "Chủ shop"}
    assert "sc_refresh" not in response.text and "refresh_token" not in response.text
    assert body["expires_in"] == 900
    cookie = response.headers["set-cookie"]
    assert all(value in cookie for value in ("HttpOnly", "Path=/api/v1/auth", "SameSite=lax"))
    from http.cookies import SimpleCookie
    parsed_cookie = SimpleCookie(cookie)["sc_refresh"]
    assert 604790 <= int(parsed_cookie["max-age"]) <= 604800
    assert response.headers["cache-control"] == "no-store"
    old_cookie = stack.client.cookies.get("sc_refresh")
    headers = {"Authorization": "Bearer " + body["access_token"]}
    assert (await stack.client.get("/api/v1/auth/me", headers=headers)).status_code == 200
    refresh = await stack.client.post("/api/v1/auth/refresh", headers=ORIGIN)
    assert refresh.status_code == 200
    assert old_cookie != stack.client.cookies.get("sc_refresh")
    # Replaying a consumed cookie cannot rotate; it does not revoke the current secret.
    replay = await stack.client.post("/api/v1/auth/refresh", headers={**ORIGIN, "Cookie": "sc_refresh=" + old_cookie})
    assert replay.status_code == 401
    assert (await stack.client.post("/api/v1/auth/refresh", headers=ORIGIN)).status_code == 200
    assert (await stack.client.post("/api/v1/auth/logout", headers={**ORIGIN, **headers})).status_code == 204
    assert (await stack.client.get("/api/v1/auth/me", headers=headers)).status_code == 401
    assert (await stack.client.post("/api/v1/auth/refresh", headers=ORIGIN)).status_code == 401
    assert (await stack.client.post("/api/v1/auth/logout", headers=ORIGIN)).status_code == 204


@pytest.mark.asyncio
async def test_wrong_email_password_and_inactive_share_error(stack):
    bad = await stack.client.post("/api/v1/auth/login", headers=ORIGIN,
                                  json={"email": stack.user.email, "password": "wrong"})
    stack.result.scalar_one_or_none.return_value = None
    missing = await login(stack)
    stack.result.scalar_one_or_none.return_value = stack.user
    stack.user.is_active = False
    inactive = await login(stack)
    assert bad.status_code == missing.status_code == inactive.status_code == 401
    assert bad.json() == missing.json() == inactive.json()
    assert not await stack.redis.keys("sc:session:*")


@pytest.mark.asyncio
@pytest.mark.parametrize("origin", [None, "https://evil.example", "null"])
@pytest.mark.parametrize("endpoint", ["login", "refresh", "logout"])
async def test_origin_required(stack, endpoint, origin):
    headers = {"Origin": origin} if origin else {}
    response = await stack.client.post("/api/v1/auth/" + endpoint, headers=headers,
                                        json={"email": stack.user.email, "password": PASSWORD})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_validation_does_not_echo_password(stack):
    response = await stack.client.post("/api/v1/auth/login", headers=ORIGIN,
                                       json={"email": "invalid", "password": PASSWORD, "extra": True})
    assert response.status_code == 422
    assert PASSWORD not in response.text


@pytest.mark.asyncio
async def test_refresh_concurrent_only_one_wins(stack):
    await login(stack)
    cookie = stack.client.cookies.get("sc_refresh")
    responses = await asyncio.gather(*[
        stack.client.post("/api/v1/auth/refresh", headers={**ORIGIN, "Cookie": "sc_refresh=" + cookie})
        for _ in range(2)])
    assert sorted(r.status_code for r in responses) == [200, 401]


@pytest.mark.asyncio
@pytest.mark.parametrize("elapsed", [86400, 604800])
async def test_idle_and_absolute_expiry(stack, monkeypatch, elapsed):
    await login(stack)
    start = security.now()
    monkeypatch.setattr(security, "now", lambda: start + elapsed)
    assert (await stack.client.post("/api/v1/auth/refresh", headers=ORIGIN)).status_code == 401


@pytest.mark.asyncio
async def test_refresh_does_not_extend_absolute_expiry(stack, monkeypatch):
    await login(stack)
    cookie = stack.client.cookies.get("sc_refresh")
    key = security.session_key(cookie.split(".")[0])
    expiry = await stack.redis.hget(key, "expires")
    start = security.now()
    monkeypatch.setattr(security, "now", lambda: start + 100)
    response = await stack.client.post("/api/v1/auth/refresh", headers=ORIGIN)
    assert response.status_code == 200
    assert await stack.redis.hget(key, "expires") == expiry


@pytest.mark.asyncio
async def test_redis_down_fails_closed(stack, monkeypatch):
    response = await login(stack)
    headers = {"Authorization": "Bearer " + response.json()["data"]["access_token"]}
    monkeypatch.setattr(stack.redis, "eval", AsyncMock(side_effect=ConnectionError("private details")))
    for response in [await stack.client.get("/api/v1/auth/me", headers=headers),
                     await stack.client.get("/api/v1/products", headers=headers),
                     await stack.client.post("/api/v1/auth/refresh", headers=ORIGIN),
                     await stack.client.post("/api/v1/auth/logout", headers=ORIGIN)]:
        assert response.status_code == 503
        assert "private details" not in response.text


@pytest.mark.asyncio
async def test_db_down_does_not_consume_refresh(stack):
    await login(stack)
    cookie = stack.client.cookies.get("sc_refresh")
    stack.db.get.side_effect = OperationalError("hidden DSN", {}, Exception())
    response = await stack.client.post("/api/v1/auth/refresh", headers=ORIGIN)
    assert response.status_code == 503 and "hidden DSN" not in response.text
    stack.db.get.side_effect = None
    assert stack.client.cookies.get("sc_refresh") == cookie
    assert (await stack.client.post("/api/v1/auth/refresh", headers=ORIGIN)).status_code == 200


@pytest.mark.asyncio
async def test_missing_cookie_logout_does_not_revoke_other_session(stack):
    response = await login(stack)
    headers = {"Authorization": "Bearer " + response.json()["data"]["access_token"]}
    stack.client.cookies.clear()
    assert (await stack.client.post("/api/v1/auth/logout", headers={**ORIGIN, **headers})).status_code == 204
    assert (await stack.client.get("/api/v1/auth/me", headers=headers)).status_code == 200


@pytest.mark.asyncio
async def test_gateway_routes_and_cors(stack):
    for path, status in [("/api/v1/products", 401), ("/api/v1/auth/me", 401),
                         ("/api/v1/products-evil", 404), ("/internal", 404), ("/internal/users", 404)]:
        assert (await stack.client.get(path)).status_code == status
    response = await stack.client.options("/api/v1/auth/login", headers={**ORIGIN,
        "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN["Origin"]
    assert response.headers["access-control-allow-credentials"] == "true"
    response = await stack.client.options("/api/v1/auth/login", headers={
        "Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 400 and "access-control-allow-origin" not in response.headers


@pytest.mark.asyncio
async def test_proxy_preserves_raw_webhook_body_and_repeated_cookies(stack, monkeypatch):
    original_client = HTTP_CLIENT
    raw = b'{ "signature-sensitive": "bytes" }\n'

    def upstream(request):
        assert request.content == raw
        assert request.headers["x-hub-signature-256"] == "sha256=fixture"
        assert "x-user-id" not in request.headers and "x-internal-token" not in request.headers
        return httpx.Response(200, content=b"ok", headers=[("set-cookie", "a=1"), ("set-cookie", "b=2")])

    monkeypatch.setattr(stack.gateway.httpx, "AsyncClient", lambda **kwargs:
                        original_client(transport=httpx.MockTransport(upstream), **kwargs))
    response = await stack.client.post("/webhooks/facebook", content=raw, headers={
        "X-Hub-Signature-256": "sha256=fixture", "X-User-Id": "spoof", "X-Internal-Token": "spoof"})
    assert response.status_code == 200 and response.content == b"ok"
    assert response.headers.get_list("set-cookie") == ["a=1", "b=2"]
    assert response.headers["content-length"] == "2"


@pytest.mark.asyncio
async def test_blacklisted_access_and_inactive_user_rejected(stack):
    response = await login(stack)
    token = response.json()["data"]["access_token"]
    headers = {"Authorization": "Bearer " + token}
    claims = security.decode_access(token)
    await stack.redis.set(f"sc:blacklist:{claims['jti']}", "1", ex=900)
    assert (await stack.client.get("/api/v1/auth/me", headers=headers)).status_code == 401
    await stack.redis.delete(f"sc:blacklist:{claims['jti']}")
    stack.user.is_active = False
    assert (await stack.client.get("/api/v1/auth/me", headers=headers)).status_code == 401
    assert (await stack.client.post("/api/v1/auth/refresh", headers=ORIGIN)).status_code == 401


@pytest.mark.parametrize("mutation", [{"exp": 0}, {"aud": "wrong"}, {"iss": "wrong"}, {"sid": "invalid"}, {"jti": None}])
def test_reject_invalid_claims(rsa_keys, mutation):
    claims = security.decode_access(security.issue_access(str(uuid4()), str(uuid4())))
    claims.update(mutation)
    token = jwt.encode(claims, rsa_keys[0].read_bytes(), algorithm="RS256")
    with pytest.raises(security.AuthError) as exc:
        security.decode_access(token)
    assert exc.value.status == 401


def test_password_long_unicode_spaces_and_legacy():
    password = " " + "mật khẩu" * 100 + " "
    hashed = hash_password(password)
    assert hashed.startswith("$argon2id$") and verify_password(password, hashed)
    assert not verify_password(password.strip(), hashed)
    assert not verify_password("wrong", hashed)
    legacy = bcrypt.hashpw(b"legacy-password", bcrypt.gensalt()).decode()
    assert verify_password("legacy-password", legacy)
    assert not verify_password("wrong", legacy)
