import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert

from app.providers import authorization_url, exchange, refresh_zalo, require_platform, send_text
from shared.auth import AuthError, Sessions
from shared.config import settings
from shared.db.models import Message, Customer, Conversation, PlatformConnection, PlatformDispatch
from shared.db.session import get_session_factory
from shared.inbox_http import DB, inbox_service, internal_token, success
from shared.provider_secrets import cipher, decrypt, encrypt
from shared.service_http import poll

Platform = Literal["facebook", "zalo"]


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def refresh_one():
    async with get_session_factory().begin() as db:
        connection = await db.scalar(select(PlatformConnection).where(
            PlatformConnection.platform == "ZALO", PlatformConnection.status == "CONNECTED",
            PlatformConnection.token_expires_at <= now() + timedelta(minutes=5)).with_for_update(skip_locked=True))
        if connection is None:
            return False
        token = decrypt(connection.encrypted_refresh_token)
        id = connection.id
        connection.status, connection.last_error_code = "ERROR", "REFRESH_IN_PROGRESS"
    # Refresh tokens rotate once. A crash leaves a visible reconnect requirement.
    try:
        tokens = await refresh_zalo(token)
        access, refresh = encrypt(tokens["access_token"]), encrypt(tokens["refresh_token"])
        expires = now() + timedelta(seconds=int(tokens["expires_in"]))
    except (AuthError, KeyError, ValueError):
        return False
    async with get_session_factory().begin() as db:
        connection = await db.get(PlatformConnection, id, with_for_update=True)
        if connection.last_error_code == "REFRESH_IN_PROGRESS":
            connection.encrypted_access_token, connection.encrypted_refresh_token = access, refresh
            connection.token_expires_at = expires
            connection.status, connection.last_error_code = "CONNECTED", None
    return True


async def token_worker():
    if settings.zalo_enabled:
        await poll(refresh_one)


app, seller = inbox_service("platform-service", background=(token_worker,))
router = APIRouter(prefix="/api/v1/connections", dependencies=[Depends(seller)])


def connection_data(row):
    return {"id": row.id, "platform": row.platform, "account_id": row.account_id,
            "account_name": row.display_name or row.account_id, "account_type": "PAGE" if row.platform == "FACEBOOK" else "OA",
            "status": row.status, "last_error_code": row.last_error_code}


@router.get("")
async def connections(db: DB):
    return success([connection_data(row) for row in await db.scalars(select(PlatformConnection).order_by(PlatformConnection.platform))])


@router.post("/{platform}/oauth/start")
async def start(platform: Platform, actor: Annotated[dict, Depends(seller)]):
    cipher()
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    url = authorization_url(platform, state, verifier)
    try:
        await app.state.redis.set("sc:oauth:" + state, json.dumps({
            "platform": platform, "token": actor, "verifier": verifier,
        }), ex=600, nx=True)
    except RedisError:
        raise AuthError(503, "SERVICE_UNAVAILABLE", "Không lưu được phiên cấp quyền") from None
    return success({"authorization_url": url})


@app.get("/api/v1/connections/{platform}/oauth/callback")
async def callback(platform: Platform, db: DB, state: Annotated[str, Query(min_length=1, max_length=500)],
                   code: Annotated[str | None, Query(max_length=2000)] = None,
                   error: Annotated[str | None, Query(max_length=500)] = None):
    try:
        stored = await app.state.redis.getdel("sc:oauth:" + state)
    except RedisError:
        raise AuthError(503, "SERVICE_UNAVAILABLE", "Không kiểm tra được phiên cấp quyền") from None
    if not stored:
        raise AuthError(403, "INVALID_STATE", "Phiên cấp quyền đã hết hạn hoặc đã dùng")
    data = json.loads(stored)
    if data["platform"] != platform:
        raise AuthError(403, "INVALID_STATE", "Nền tảng không khớp phiên cấp quyền")
    # Recheck session and access jti before exchanging a provider code.
    claims = data["token"]
    from shared.auth import _PASSIVE, session_key
    result = await app.state.redis.eval(_PASSIVE, 2, session_key(claims["sid"]), f"sc:blacklist:{claims['jti']}",
                                       int(datetime.now(timezone.utc).timestamp()), 86400, claims["sub"])
    if not result:
        raise AuthError(403, "SESSION_REVOKED", "Phiên bắt đầu cấp quyền đã bị thu hồi")
    if error:
        return RedirectResponse(settings.frontend_url.rstrip("/") + "/settings?connected=0", status_code=302)
    if not code:
        raise AuthError(400, "CODE_REQUIRED", "Thiếu mã cấp quyền")
    try:
        account = await exchange(platform, code, data["verifier"])
        access = encrypt(account["access_token"])
        refresh = encrypt(account["refresh_token"]) if account.get("refresh_token") else None
        lifetime = int(account.get("expires_in") or account.get("expire_in") or 0)
        if platform == "zalo" and (not refresh or lifetime <= 0):
            raise ValueError
        account_id, name = account["account_id"], account["name"]
    except (KeyError, ValueError, TypeError, AttributeError):
        raise AuthError(503, "PROVIDER_RESPONSE_INVALID", "Phản hồi cấp quyền không hợp lệ. Hãy kết nối lại") from None
    stmt = insert(PlatformConnection).values(platform=platform.upper(), account_id=account_id,
        display_name=name, status="CONNECTED", encrypted_access_token=access, encrypted_refresh_token=refresh,
        token_expires_at=now() + timedelta(seconds=lifetime) if lifetime else None)
    await db.execute(stmt.on_duplicate_key_update(account_id=stmt.inserted.account_id, display_name=stmt.inserted.display_name,
        status="CONNECTED", encrypted_access_token=stmt.inserted.encrypted_access_token,
        encrypted_refresh_token=stmt.inserted.encrypted_refresh_token, token_expires_at=stmt.inserted.token_expires_at,
        last_error_code=None))
    await db.commit()
    return RedirectResponse(settings.frontend_url.rstrip("/") + "/settings?connected=1", status_code=302)


@router.delete("/{platform}", status_code=204)
async def disconnect(platform: Platform, db: DB):
    row = await db.scalar(select(PlatformConnection).where(PlatformConnection.platform == platform.upper()).with_for_update())
    if row:
        row.status, row.last_error_code = "DISCONNECTED", None
        row.encrypted_access_token = row.encrypted_refresh_token = row.token_expires_at = None
        await db.commit()
    return Response(status_code=204)


class Dispatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attempt_id: UUID


@app.post("/internal/messages/{message_id}/dispatch", dependencies=[Depends(internal_token)])
async def dispatch(message_id: UUID, body: Dispatch, db: DB):
    digest = hashlib.sha256(str(message_id).encode()).hexdigest()
    created = True
    try:
        async with db.begin_nested():
            db.add(PlatformDispatch(id=str(body.attempt_id), message_id=str(message_id), request_hash=digest))
            await db.flush()
    except IntegrityError:
        created = False
    claim = await db.scalar(select(PlatformDispatch).where(PlatformDispatch.id == str(body.attempt_id)).with_for_update())
    if claim.request_hash != digest:
        raise AuthError(409, "ATTEMPT_CONFLICT", "Mã lần gửi đã dùng cho tin khác")
    if not created:
        await db.commit()
        return success(claim.result or {"accepted": False, "delivery_unknown": True, "error_code": "DELIVERY_UNKNOWN"})
    await db.commit()
    row = await db.get(Message, str(message_id))
    if row is None:
        raise AuthError(404, "NOT_FOUND", "Không tìm thấy tin cần gửi")
    conv = await db.get(Conversation, row.conversation_id)
    customer = await db.get(Customer, conv.customer_id)
    connection = await db.scalar(select(PlatformConnection).where(
        PlatformConnection.platform == row.platform, PlatformConnection.account_id == row.platform_account_id).with_for_update())
    outcome = {"accepted": False, "delivery_unknown": False, "error_code": "PLATFORM_DISCONNECTED"}
    if row.status == "SENT":
        outcome = {"accepted": True, "delivery_unknown": False, "provider_message_id": row.platform_msg_id}
    elif row.status != "SENDING" or row.sender != "SELLER":
        outcome["error_code"] = "MESSAGE_NOT_SENDABLE"
    elif connection is not None and connection.status == "CONNECTED":
        try:
            require_platform(row.platform.lower())
            if connection.token_expires_at and connection.token_expires_at <= now():
                raise AuthError(503, "TOKEN_EXPIRED", "Cần làm mới token")
            outcome = await send_text(row.platform, connection.account_id, customer.platform_user_id,
                                      decrypt(connection.encrypted_access_token), row.content)
        except AuthError as exc:
            outcome["error_code"] = exc.code
    claim = await db.get(PlatformDispatch, str(body.attempt_id), with_for_update=True)
    claim.result = outcome
    if connection is not None and outcome.get("error_code") in ("FACEBOOK_190", "ZALO_-124", "ZALO_-216"):
        connection.status, connection.last_error_code = "ERROR", outcome["error_code"]
    await db.commit()
    return success(outcome)


app.include_router(router)
