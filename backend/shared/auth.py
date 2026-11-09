"""RS256 verification and Redis sessions shared by auth and Gateway.

Only auth-service calls issue_access() and reads the private key.
Redis scripts keep rotation, idle checks and revocation atomic.
"""
from __future__ import annotations

import hashlib
import secrets
import time
from pathlib import Path
from uuid import UUID, uuid4

import jwt
from fastapi import Request
from redis.exceptions import RedisError

from shared.config import settings


class AuthError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def unauthorized():
    return AuthError(401, "UNAUTHORIZED", "Phiên đăng nhập không hợp lệ hoặc đã hết hạn")


def unavailable():
    return AuthError(503, "SERVICE_UNAVAILABLE", "Dịch vụ xác thực tạm thời không sẵn sàng")


def error_body(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message, "details": []}}


def check_origin(request: Request) -> None:
    if request.headers.get("origin") not in settings.cors_allowed_origins:
        raise AuthError(403, "FORBIDDEN", "Origin không được phép")


def now() -> int:
    return int(time.time())


def session_key(sid: str) -> str:
    return f"sc:session:{sid}"


def refresh_hash(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def parse_refresh(cookie: str | None) -> tuple[str, str]:
    try:
        sid, secret = (cookie or "").split(".", 1)
        if str(UUID(sid)) != sid or len(secret) != 43:
            raise ValueError
        return sid, secret
    except ValueError:
        raise unauthorized() from None


def issue_access(uid: str, sid: str) -> str:
    issued = now()
    claims = {"sub": uid, "sid": sid, "jti": str(uuid4()), "iat": issued,
              "exp": issued + 900, "iss": settings.jwt_issuer, "aud": settings.jwt_audience}
    try:
        return jwt.encode(claims, Path(settings.jwt_private_key_path).read_bytes(), algorithm="RS256")
    except (OSError, ValueError, jwt.PyJWTError):
        raise unavailable() from None


def decode_access(token: str) -> dict:
    try:
        key = Path(settings.jwt_public_key_path).read_bytes()
    except OSError:
        raise unavailable() from None
    try:
        claims = jwt.decode(token, key, algorithms=["RS256"], issuer=settings.jwt_issuer,
                            audience=settings.jwt_audience,
                            options={"require": ["sub", "sid", "jti", "iat", "exp", "iss", "aud"]})
        for field in ("sub", "sid", "jti"):
            if str(UUID(claims[field])) != claims[field]:
                raise ValueError
        if (type(claims["iat"]) is not int or type(claims["exp"]) is not int
                or not 0 < claims["exp"] - claims["iat"] <= 900):
            raise ValueError
        return claims
    except (jwt.InvalidKeyError, NotImplementedError):
        raise unavailable() from None
    except (jwt.PyJWTError, ValueError, TypeError, AttributeError):
        raise unauthorized() from None


# ARGV: now, idle, [expected hash, new hash]. Redis keeps absolute expiry
# across refreshes; only authenticated activity advances last_seen.
_CHECK = """
local uid = redis.call('HGET', KEYS[1], 'uid')
if not uid then return {} end
local expiry = tonumber(redis.call('HGET', KEYS[1], 'expires'))
local seen = tonumber(redis.call('HGET', KEYS[1], 'last_seen'))
local now = tonumber(ARGV[1])
if now >= expiry or now - seen >= tonumber(ARGV[2]) then
    redis.call('DEL', KEYS[1]); return {}
end
"""
_ROTATE = _CHECK + """
if redis.call('HGET', KEYS[1], 'refresh_hash') ~= ARGV[3] then return {} end
redis.call('HSET', KEYS[1], 'refresh_hash', ARGV[4], 'last_seen', ARGV[1])
return {uid, tostring(expiry)}
"""
_LOOKUP = _CHECK + """
if redis.call('HGET', KEYS[1], 'refresh_hash') ~= ARGV[3] then return {} end
return {uid}
"""
_TOUCH = _CHECK + """
if uid ~= ARGV[3] or redis.call('EXISTS', KEYS[2]) == 1 then return {} end
redis.call('HSET', KEYS[1], 'last_seen', ARGV[1])
return {uid}
"""
_LOGOUT = """
if redis.call('HGET', KEYS[1], 'refresh_hash') ~= ARGV[1] then return 0 end
redis.call('DEL', KEYS[1])
if tonumber(ARGV[2]) > 0 then redis.call('SET', KEYS[2], '1', 'EX', ARGV[2]) end
return 1
"""


class Sessions:
    def __init__(self, redis):
        self.redis = redis

    async def create(self, uid: str, sid: str) -> tuple[str, str, int]:
        secret = secrets.token_urlsafe(32)
        issued = now()
        expiry = issued + 604800
        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.hset(session_key(sid), mapping={"uid": uid, "refresh_hash": refresh_hash(secret),
                                                     "last_seen": issued, "expires": expiry})
                pipe.expireat(session_key(sid), expiry)
                await pipe.execute()
        except RedisError:
            raise unavailable() from None
        return sid, f"{sid}.{secret}", expiry

    async def rotate(self, cookie: str | None) -> tuple[str, str, str, int]:
        sid, old_secret = parse_refresh(cookie)
        secret = secrets.token_urlsafe(32)
        try:
            result = await self.redis.eval(_ROTATE, 1, session_key(sid), now(), 86400,
                                           refresh_hash(old_secret), refresh_hash(secret))
        except RedisError:
            raise unavailable() from None
        if not result:
            raise unauthorized()
        return result[0], sid, f"{sid}.{secret}", int(result[1])

    async def lookup_refresh(self, cookie: str | None) -> str:
        sid, secret = parse_refresh(cookie)
        try:
            result = await self.redis.eval(_LOOKUP, 1, session_key(sid), now(), 86400, refresh_hash(secret))
        except RedisError:
            raise unavailable() from None
        if not result:
            raise unauthorized()
        return result[0]

    async def authorize(self, authorization: str | None) -> dict:
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise unauthorized()
        claims = decode_access(token)
        try:
            result = await self.redis.eval(_TOUCH, 2, session_key(claims["sid"]),
                                           f"sc:blacklist:{claims['jti']}", now(), 86400, claims["sub"])
        except RedisError:
            raise unavailable() from None
        if not result:
            raise unauthorized()
        return claims

    async def logout(self, cookie: str | None, authorization: str | None) -> None:
        if not cookie:
            return
        try:
            sid, secret = parse_refresh(cookie)
        except AuthError:
            return
        jti, ttl = "none", 0
        if authorization:
            try:
                claims = decode_access(authorization.removeprefix("Bearer "))
                if claims["sid"] == sid:
                    jti, ttl = claims["jti"], max(0, claims["exp"] - now())
            except AuthError as exc:
                if exc.status != 401:
                    raise
        try:
            await self.redis.eval(_LOGOUT, 2, session_key(sid), f"sc:blacklist:{jti}",
                                  refresh_hash(secret), ttl)
        except RedisError:
            raise unavailable() from None
