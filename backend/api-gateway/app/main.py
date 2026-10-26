"""API Gateway — port 8000.

Phạm vi BOOT-01:
  - /health         kiểm tra DB và Redis, trả 503 nếu thiếu
  - /api/v1/*       proxy đến service tương ứng (stub, hoàn thiện ở AUTH-01+)
  - /webhooks/*     proxy đến webhook-service (stub)

Chú ý: Gateway không expose /internal/*; CORS chỉ cho origins trong allowlist;
webhook bỏ JWT nhưng giữ signature header; không expose DSN trong error.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from shared.config import settings
from shared.db.session import db_lifespan, get_engine

# ── Redis client (module-level; closed on shutdown) ───────────────────────────
_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_lifespan():
        redis_client = get_redis()
        try:
            yield
        finally:
            await redis_client.aclose()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SocialCart API Gateway",
    version="0.1.0",
    docs_url=None,         # Không expose docs ở Gateway; mỗi service có swagger riêng
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
async def health_check():
    """
    Kiểm tra DB và Redis.
    200 khi cả hai sẵn sàng; 503 khi ít nhất một dependency lỗi.
    Không lộ connection string hay chi tiết lỗi nội bộ.
    """
    checks: dict[str, str] = {}
    ok = True

    # Kiểm DB
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "error"
        ok = False

    # Kiểm Redis
    try:
        redis_client = get_redis()
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"
        ok = False

    status_code = 200 if ok else 503
    return JSONResponse(
        status_code=status_code,
        content={"success": ok, "checks": checks},
    )


# ── Proxy helpers ─────────────────────────────────────────────────────────────

_ROUTE_MAP: dict[str, str] = {
    "/api/v1/auth": settings.auth_service_url,
    "/api/v1/conversations": settings.conversation_service_url,
    "/api/v1/customers": settings.customer_service_url,
    "/api/v1/products": settings.product_service_url,
    "/api/v1/orders": settings.order_service_url,
    "/api/v1/ai": settings.ai_service_url,
    "/api/v1/connections": settings.platform_service_url,
    "/api/v1/dashboard": settings.dashboard_service_url,
    "/api/v1/settings": settings.ai_service_url,   # FAQ/config qua ai-service
    "/webhooks": settings.webhook_service_url,
}


def _resolve_upstream(path: str) -> str | None:
    """Tìm upstream URL cho path; trả None nếu không khớp."""
    for prefix, url in _ROUTE_MAP.items():
        if path.startswith(prefix):
            return url
    return None


async def _proxy(request: Request, upstream_url: str) -> Response:
    """Chuyển tiếp request đến upstream, giữ headers và body."""
    path = request.url.path
    query = request.url.query
    target = f"{upstream_url}{path}"
    if query:
        target = f"{target}?{query}"

    # Lọc bỏ hop-by-hop headers
    _HOP_BY_HOP = {"connection", "keep-alive", "transfer-encoding", "te", "upgrade", "proxy-authorization"}
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }

    body = await request.body()

    async with httpx.AsyncClient(timeout=30.0) as client:
        upstream_resp = await client.request(
            method=request.method,
            url=target,
            headers=headers,
            content=body,
        )

    # Lọc response headers
    resp_headers = {
        k: v for k, v in upstream_resp.headers.items()
        if k.lower() not in {"transfer-encoding", "content-encoding"}
    }

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
    )


# ── Catch-all proxy ────────────────────────────────────────────────────────────

@app.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def gateway_proxy(request: Request, full_path: str):
    """Forward đến upstream service theo route map."""
    path = request.url.path

    # Chặn /internal/*
    if path.startswith("/internal/"):
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": {"code": "NOT_FOUND", "message": "Not found"}},
        )

    upstream = _resolve_upstream(path)
    if upstream is None:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": {"code": "NOT_FOUND", "message": "Route not found"}},
        )

    try:
        return await _proxy(request, upstream)
    except httpx.ConnectError:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": {"code": "SERVICE_UNAVAILABLE", "message": "Upstream unavailable"}},
        )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"success": False, "error": {"code": "GATEWAY_TIMEOUT", "message": "Upstream timeout"}},
        )
