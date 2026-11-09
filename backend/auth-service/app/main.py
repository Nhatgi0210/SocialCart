"""Seller authentication. Browser requests enter via Gateway /api/v1/auth."""
from contextlib import asynccontextmanager
from uuid import uuid4

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from shared.auth import (AuthError, Sessions, check_origin, error_body,
                         issue_access, now, parse_refresh, unauthorized, unavailable)
from shared.config import settings
from shared.db.models import User
from shared.db.session import db_lifespan, get_session
from shared.health import readiness
from shared.passwords import verify_password

_redis = None


def get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True,
                                  socket_connect_timeout=3, socket_timeout=3)
    return _redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis
    async with db_lifespan():
        try:
            yield
        finally:
            if _redis is not None:
                await _redis.aclose()
                _redis = None


app = FastAPI(title="SocialCart Auth Service", version="0.2.0", lifespan=lifespan)


@app.exception_handler(AuthError)
async def auth_error(request: Request, exc: AuthError):
    return JSONResponse(status_code=exc.status, content=error_body(exc.code, exc.message),
                        headers={"Cache-Control": "no-store"})


@app.exception_handler(SQLAlchemyError)
async def db_error(request: Request, exc: SQLAlchemyError):
    return await auth_error(request, unavailable())


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Never echo the invalid input: it may contain a password.
    return JSONResponse(status_code=422, content=error_body("VALIDATION_ERROR", "Dữ liệu không hợp lệ"))


@app.get("/health")
async def health_check():
    return await readiness("auth-service", get_redis())


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=1, max_length=1024)


def user_data(user: User) -> dict:
    return {"id": user.id, "email": user.email, "name": user.name}


async def active_user(db: AsyncSession, uid: str) -> User:
    user = await db.get(User, uid)
    if user is None or not user.is_active:
        raise unauthorized()
    return user


def token_response(user: User, access: str, cookie: str, expiry: int) -> JSONResponse:
    response = JSONResponse(content={"success": True, "data": {
        "access_token": access, "token_type": "bearer", "expires_in": 900, "user": user_data(user)}},
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"})
    response.set_cookie("sc_refresh", cookie, max_age=max(0, expiry - now()),
                        httponly=True, secure=settings.refresh_cookie_secure,
                        samesite="lax", path="/api/v1/auth")
    return response


@app.post("/api/v1/auth/login", dependencies=[Depends(check_origin)])
async def login(payload: Login, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(User).where(User.email == str(payload.email)))
    user = result.scalar_one_or_none()
    valid = await run_in_threadpool(verify_password, payload.password, user.hashed_password if user else None)
    if not valid or user is None or not user.is_active:
        raise AuthError(401, "UNAUTHORIZED", "Email hoặc mật khẩu không đúng")
    # Check signing configuration before persisting a usable session.
    sid = str(uuid4())
    access = issue_access(user.id, sid)
    _, cookie, expiry = await Sessions(get_redis()).create(user.id, sid)
    return token_response(user, access, cookie, expiry)


@app.post("/api/v1/auth/refresh", dependencies=[Depends(check_origin)])
async def refresh(request: Request, db: AsyncSession = Depends(get_session)):
    cookie_in = request.cookies.get("sc_refresh")
    sessions = Sessions(get_redis())
    uid = await sessions.lookup_refresh(cookie_in)
    user = await active_user(db, uid)
    # Preflight signing key before consuming the single-use refresh secret.
    sid, _ = parse_refresh(cookie_in)
    access = issue_access(uid, sid)
    uid, sid, cookie, expiry = await sessions.rotate(cookie_in)
    return token_response(user, access, cookie, expiry)


@app.get("/api/v1/auth/me")
async def me(request: Request, db: AsyncSession = Depends(get_session)):
    claims = await Sessions(get_redis()).authorize(request.headers.get("authorization"))
    user = await active_user(db, claims["sub"])
    return JSONResponse(content={"success": True, "data": user_data(user)}, headers={"Cache-Control": "no-store"})


@app.post("/api/v1/auth/logout", dependencies=[Depends(check_origin)], status_code=204)
async def logout(request: Request):
    await Sessions(get_redis()).logout(request.cookies.get("sc_refresh"), request.headers.get("authorization"))
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie("sc_refresh", path="/api/v1/auth", httponly=True,
                           secure=settings.refresh_cookie_secure, samesite="lax")
    return response
