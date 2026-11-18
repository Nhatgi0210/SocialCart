from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select

from shared.auth import AuthError
from shared.db.models import Conversation, ConversationOutbox, Customer, Message, RealtimeOutbox
from shared.inbox_http import DB, Limit, Page, Platform, customer_data, inbox_service, paged, success, utc
from shared.idempotency import run_mutation
from app.delivery import message_data, outgoing_worker
from app.incoming import register_incoming

app, seller = inbox_service("conversation-service", background=(outgoing_worker,))
register_incoming(app)
router = APIRouter(prefix="/api/v1/conversations", dependencies=[Depends(seller)])
Status = Literal["NEW", "IN_PROGRESS", "RESOLVED"]
AIStatus = Literal["AI_HANDLING", "NEEDS_SELLER", "SELLER_HANDLING"]
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=100)]
Seller = Annotated[dict, Depends(seller)]


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: Annotated[str, Field(min_length=1, max_length=2000)]

    @field_validator("content")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Message is blank")
        return value


class ReadUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_read: Literal[True]

    @field_validator("is_read", mode="before")
    @classmethod
    def require_true(cls, value):
        if value is not True:
            raise ValueError("is_read must be true")
        return value


class VersionedUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: Annotated[int, Field(strict=True, ge=1, le=2147483647)]


class StatusUpdate(VersionedUpdate):
    status: Status


class AIUpdate(VersionedUpdate):
    ai_status: Literal["AI_HANDLING", "SELLER_HANDLING"]


recent_message = (select(func.left(Message.content, 200)).where(Message.conversation_id == Conversation.id)
                  .order_by(Message.created_at.desc(), Message.id.desc()).limit(1).scalar_subquery())
summary = select(Conversation, Customer, recent_message).join(Customer, Customer.id == Conversation.customer_id)


def conversation_data(conversation, customer, preview):
    return {
        "id": conversation.id, "platform": conversation.platform, "customer": customer_data(customer),
        "status": conversation.status, "ai_status": conversation.ai_status, "is_read": conversation.is_read,
        "last_message_at": utc(conversation.last_message_at or conversation.created_at),
        "last_message_preview": preview or "", "version": conversation.version, "created_at": utc(conversation.created_at),
    }


async def find_conversation(db: DB, id: UUID, *, lock=False):
    statement = select(Conversation).where(Conversation.id == str(id))
    conversation = await db.scalar(statement.with_for_update() if lock else statement)
    if conversation is None:
        raise AuthError(404, "NOT_FOUND", "Không tìm thấy hội thoại")
    return conversation


async def read_summary(db: DB, id: UUID):
    row = (await db.execute(summary.where(Conversation.id == str(id)))).one_or_none()
    if row is None:
        raise AuthError(404, "NOT_FOUND", "Không tìm thấy hội thoại")
    return success(conversation_data(*row))


@router.get("")
async def list_conversations(db: DB, page: Page = 1, limit: Limit = 20, platform: Platform | None = None,
                             status: Status | None = None, ai_status: AIStatus | None = None,
                             customer_id: UUID | None = None, is_read: bool | None = None):
    filters = []
    for column, value in ((Conversation.platform, platform), (Conversation.status, status),
                          (Conversation.ai_status, ai_status), (Conversation.customer_id, customer_id),
                          (Conversation.is_read, is_read)):
        if value is not None:
            filters.append(column == (str(value) if isinstance(value, UUID) else value))
    total = await db.scalar(select(func.count()).select_from(Conversation).where(*filters))
    rows = await db.execute(summary.where(*filters)
                            .order_by(func.coalesce(Conversation.last_message_at, Conversation.created_at).desc(),
                                      Conversation.id.desc()).offset((page - 1) * limit).limit(limit))
    return paged([conversation_data(*row) for row in rows], page, limit, total)


@router.get("/{id}")
async def get_conversation(id: UUID, db: DB):
    return await read_summary(db, id)


@router.patch("/{id}/read")
async def mark_read(id: UUID, body: ReadUpdate, db: DB):
    conversation = await find_conversation(db, id, lock=True)
    if not conversation.is_read:
        conversation.is_read = body.is_read
        conversation.version += 1
        queue_update(db, conversation)
    await db.commit()
    return await read_summary(db, id)


def check_version(conversation: Conversation, expected: int):
    if conversation.version != expected:
        raise AuthError(409, "VERSION_CONFLICT", "Hội thoại đã thay đổi. Vui lòng tải lại.")


def queue_update(db, conversation):
    db.add(RealtimeOutbox(event_type="conversation:updated", data={
        "conversation_id": conversation.id, "version": conversation.version,
    }))


@router.patch("/{id}/status")
async def set_status(id: UUID, body: StatusUpdate, db: DB):
    conversation = await find_conversation(db, id, lock=True)
    check_version(conversation, body.expected_version)
    if conversation.status != body.status:
        conversation.status = body.status
        conversation.version += 1
        queue_update(db, conversation)
    await db.commit()
    return await read_summary(db, id)


@router.patch("/{id}/ai-status")
async def set_ai_status(id: UUID, body: AIUpdate, db: DB):
    conversation = await find_conversation(db, id, lock=True)
    check_version(conversation, body.expected_version)
    if conversation.ai_status != body.ai_status:
        conversation.ai_status = body.ai_status
        conversation.ai_generation += 1
        conversation.version += 1
        queue_update(db, conversation)
    await db.commit()
    return await read_summary(db, id)


@router.get("/{id}/messages")
async def list_messages(id: UUID, db: DB, page: Page = 1, limit: Limit = 20):
    await find_conversation(db, id)
    condition = Message.conversation_id == str(id)
    total = await db.scalar(select(func.count()).select_from(Message).where(condition))
    rows = await db.scalars(select(Message).where(condition).order_by(Message.created_at, Message.id)
                            .offset((page - 1) * limit).limit(limit))
    return paged([{
        "id": row.id, "conversation_id": row.conversation_id, "sender": row.sender, "content": row.content,
        "status": row.status, "platform_msg_id": row.platform_msg_id, "error_code": row.error_code,
        "delivery_unknown": row.delivery_unknown, "created_at": utc(row.created_at),
    } for row in rows], page, limit, total)


@router.post("/{id}/messages", status_code=202)
async def send_message(id: UUID, body: MessageCreate, key: Key, actor: Seller, db: DB):
    async def mutate():
        conv = await find_conversation(db, id, lock=True)
        row = Message(conversation_id=conv.id, platform=conv.platform, platform_account_id=conv.platform_account_id,
                      sender="SELLER", content=body.content, status="SENDING")
        db.add(row)
        conv.ai_status = "SELLER_HANDLING"
        conv.ai_generation += 1
        conv.version += 1
        queue_update(db, conv)
        await db.flush()
        db.add(ConversationOutbox(conversation_id=conv.id, message_id=row.id))
        db.add(RealtimeOutbox(event_type="message:new", data={"conversation_id": conv.id, "message_id": row.id}))
        return success(message_data(row))

    return await run_mutation(db, actor["sub"], "message.send", key, {"id": str(id), **body.model_dump()}, mutate)


@router.post("/{id}/messages/{message_id}/retry", status_code=202)
async def retry_message(id: UUID, message_id: UUID, key: Key, actor: Seller, db: DB):
    async def mutate():
        conv = await find_conversation(db, id, lock=True)
        job = await db.scalar(select(ConversationOutbox).where(ConversationOutbox.message_id == str(message_id)).with_for_update())
        row = await db.get(Message, str(message_id), with_for_update=True)
        if row is None or row.conversation_id != conv.id or job is None:
            raise AuthError(404, "NOT_FOUND", "Không tìm thấy tin cần gửi lại")
        if row.delivery_unknown:
            raise AuthError(409, "DELIVERY_UNKNOWN", "Chưa xác định kết quả gửi. Kiểm tra trên nền tảng trước khi gửi tin mới")
        if row.status != "FAILED":
            raise AuthError(409, "INVALID_TRANSITION", "Chỉ gửi lại tin đã thất bại")
        row.status, row.error_code = "SENDING", None
        job.status, job.attempt_count, job.next_attempt_at = "PENDING", 0, None
        conv.ai_status = "SELLER_HANDLING"
        conv.ai_generation += 1
        conv.version += 1
        queue_update(db, conv)
        db.add(RealtimeOutbox(event_type="message:updated", data={
            "conversation_id": conv.id, "message_id": row.id, "status": row.status,
        }))
        await db.flush()
        return success(message_data(row))

    return await run_mutation(db, actor["sub"], "message.retry", key, {"id": str(id), "message_id": str(message_id)}, mutate)


app.include_router(router)
