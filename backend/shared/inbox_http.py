"""HTTP conventions shared by the customer and conversation services."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from secrets import compare_digest
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException

from shared.auth import AuthError, Sessions, error_body, unavailable
from shared.config import settings
from shared.db.models import Customer
from shared.db.session import db_lifespan, get_session
from shared.health import readiness

DB = Annotated[AsyncSession, Depends(get_session)]
Platform = Literal["FACEBOOK", "ZALO"]
Page = Annotated[int, Query(ge=1, le=2147483647)]
Limit = Annotated[int, Query(ge=1, le=100)]


def inbox_service(name: str):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with db_lifespan():
            try:
                yield
            finally:
                await redis.aclose()

    redis = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=3, socket_timeout=3)
    app = FastAPI(title=name, lifespan=lifespan)

    @app.exception_handler(AuthError)
    async def auth_error(_request, exc):
        return JSONResponse(error_body(exc.code, exc.message), status_code=exc.status)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(_request, _exc):
        return await auth_error(_request, unavailable())

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, _exc):
        return JSONResponse(error_body("VALIDATION_ERROR", "Dữ liệu không hợp lệ"), status_code=422)

    @app.exception_handler(HTTPException)
    async def http_error(_request, exc):
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "REQUEST_ERROR")
        return JSONResponse(error_body(code, str(exc.detail)), status_code=exc.status_code, headers=exc.headers)

    @app.get("/health")
    async def health():
        return await readiness(name, redis)

    async def seller(authorization: Annotated[str | None, Header()] = None):
        await Sessions(redis).authorize(authorization)

    return app, seller


def internal_token(authorization: Annotated[str | None, Header()] = None):
    expected = settings.internal_service_token
    if not expected or not compare_digest((authorization or "").encode(), f"Bearer {expected}".encode()):
        raise AuthError(403, "FORBIDDEN", "Yêu cầu nội bộ không được phép")


def utc(value: datetime) -> str:
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def success(data):
    return {"success": True, "data": data}


def paged(data, page: int, limit: int, total: int):
    return {**success(data), "meta": {"page": page, "limit": limit, "total": total}}


def customer_data(customer: Customer):
    return {
        "id": customer.id,
        "platform": customer.platform,
        "platform_account_id": customer.platform_account_id,
        "platform_user_id": customer.platform_user_id,
        "name": customer.display_name or "Khách chưa có tên",
        "created_at": utc(customer.created_at),
    }
