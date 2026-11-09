"""Gateway: public auth/webhooks, authenticated business API, no internal routes."""
from contextlib import asynccontextmanager

import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.auth import AuthError, Sessions, error_body
from shared.config import settings
from shared.db.session import db_lifespan
from shared.health import readiness

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


app = FastAPI(title="SocialCart API Gateway", version="0.2.0",
              docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_allowed_origins, allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-Id"],
    expose_headers=["X-Request-Id"],
)


@app.exception_handler(AuthError)
async def auth_error(request: Request, exc: AuthError):
    return JSONResponse(status_code=exc.status, content=error_body(exc.code, exc.message),
                        headers={"Cache-Control": "no-store"})


@app.get("/health")
async def health_check():
    return await readiness("api-gateway", get_redis())


_ROUTE_MAP = {
    "/api/v1/auth": settings.auth_service_url,
    "/api/v1/conversations": settings.conversation_service_url,
    "/api/v1/customers": settings.customer_service_url,
    "/api/v1/products": settings.product_service_url,
    "/api/v1/orders": settings.order_service_url,
    "/api/v1/ai": settings.ai_service_url,
    "/api/v1/connections": settings.platform_service_url,
    "/api/v1/dashboard": settings.dashboard_service_url,
    "/api/v1/settings": settings.ai_service_url,
    "/webhooks": settings.webhook_service_url,
}
_PUBLIC = {("POST", f"/api/v1/auth/{action}") for action in ("login", "refresh", "logout")}
_HOP = {"connection", "keep-alive", "transfer-encoding", "te", "upgrade", "trailer",
        "proxy-authorization", "proxy-authenticate"}


def _resolve_upstream(path: str) -> str | None:
    for prefix, url in _ROUTE_MAP.items():
        if path == prefix or path.startswith(prefix + "/"):
            return url
    return None


def filtered_headers(headers, *, request=False):
    excluded = _HOP | {part.strip().lower() for part in headers.get("connection", "").split(",")}
    excluded |= {"host", "content-length"} if request else {"content-length", "content-encoding"}
    # Identity headers from the browser must never become trusted internal identity.
    if request:
        excluded |= {"x-user-id", "x-session-id", "x-internal-token"}
    items = headers.items() if request else headers.multi_items()
    return [(key, value) for key, value in items if key.lower() not in excluded]


async def _proxy(request: Request, upstream_url: str) -> Response:
    target = f"{upstream_url}{request.url.path}"
    if request.url.query:
        target += f"?{request.url.query}"
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        upstream = await client.request(request.method, target,
                                        headers=filtered_headers(request.headers, request=True),
                                        content=await request.body())
    response = Response(content=upstream.content, status_code=upstream.status_code)
    # Preserve repeated Set-Cookie headers and recalculate length after decompression.
    for key, value in filtered_headers(upstream.headers):
        response.headers.append(key, value)
    return response


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
               include_in_schema=False)
async def gateway_proxy(request: Request, full_path: str):
    path = request.url.path
    upstream = _resolve_upstream(path)
    if upstream is None:
        return JSONResponse(status_code=404, content=error_body("NOT_FOUND", "Route not found"))
    if (request.method, path) not in _PUBLIC and not path.startswith("/webhooks/"):
        await Sessions(get_redis()).authorize(request.headers.get("authorization"))
    try:
        return await _proxy(request, upstream)
    except httpx.TimeoutException:
        return JSONResponse(status_code=504, content=error_body("GATEWAY_TIMEOUT", "Upstream timeout"))
    except httpx.RequestError:
        return JSONResponse(status_code=503, content=error_body("SERVICE_UNAVAILABLE", "Upstream unavailable"))
