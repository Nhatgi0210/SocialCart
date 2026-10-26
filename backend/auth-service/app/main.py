"""
Auth service — port 8001.

Phạm vi BOOT-01 (shell):
  - Cấu trúc app, lifespan, CORS cơ bản
  - /health kiểm tra DB và Redis
  - Placeholder routers cho AUTH-01 implement đầy đủ

AUTH-01 sẽ implement: POST /api/v1/auth/login, GET /api/v1/auth/me,
POST /api/v1/auth/refresh, POST /api/v1/auth/logout.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from shared.config import settings
from shared.db.session import db_lifespan, get_engine

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_lifespan():
        redis_client = get_redis()
        try:
            yield
        finally:
            await redis_client.aclose()


app = FastAPI(
    title="SocialCart Auth Service",
    version="0.1.0",
    lifespan=lifespan,
    root_path="/api/v1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health", tags=["ops"])
async def health_check():
    """Kiểm tra DB và Redis; trả 503 nếu dependency lỗi."""
    checks: dict[str, str] = {}
    ok = True

    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "error"
        ok = False

    try:
        redis_client = get_redis()
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"
        ok = False

    return JSONResponse(
        status_code=200 if ok else 503,
        content={"success": ok, "checks": checks},
    )


# ── Placeholder: AUTH-01 sẽ mount routers ở đây ──────────────────────────────
# from app.routers import auth as auth_router
# app.include_router(auth_router.router, prefix="/auth")
