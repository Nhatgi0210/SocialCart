from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert

from shared.auth import AuthError
from shared.db.models import Conversation, Customer, Message, RealtimeOutbox
from shared.inbox_http import DB, internal_token, success

Identity = Annotated[str, StringConstraints(min_length=1, max_length=255)]


class Incoming(BaseModel):
    model_config = ConfigDict(extra="forbid")
    platform: Literal["FACEBOOK", "ZALO"]
    account_id: Identity
    platform_chat_id: Identity
    customer_id: UUID
    platform_msg_id: Identity
    text: Annotated[str, StringConstraints(min_length=1, max_length=10000)]
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None:
            raise ValueError("Timestamp must have timezone")
        return value


def register_incoming(app):
    @app.post("/internal/incoming-messages", dependencies=[Depends(internal_token)])
    async def receive(body: Incoming, db: DB):
        customer = await db.get(Customer, str(body.customer_id))
        if customer is None or (customer.platform, customer.platform_account_id) != (body.platform, body.account_id):
            raise AuthError(422, "VALIDATION_ERROR", "Khách hàng không khớp tài khoản nhận tin")
        stmt = insert(Conversation).values(platform=body.platform, platform_account_id=body.account_id,
            platform_chat_id=body.platform_chat_id, customer_id=str(body.customer_id))
        await db.execute(stmt.on_duplicate_key_update(id=Conversation.id))
        conv = await db.scalar(select(Conversation).where(Conversation.platform == body.platform,
            Conversation.platform_account_id == body.account_id, Conversation.platform_chat_id == body.platform_chat_id).with_for_update())
        if conv.customer_id != customer.id or customer.platform_user_id != body.platform_chat_id:
            raise AuthError(422, "VALIDATION_ERROR", "Hội thoại không khớp người gửi")
        prior = await db.scalar(select(Message).where(Message.platform == body.platform,
            Message.platform_account_id == body.account_id, Message.platform_msg_id == body.platform_msg_id))
        if prior is not None:
            await db.commit()
            return success({"conversation_id": prior.conversation_id, "message_id": prior.id})
        from datetime import timezone
        occurred = body.occurred_at.astimezone(timezone.utc).replace(tzinfo=None)
        row = Message(conversation_id=conv.id, platform=body.platform, platform_account_id=body.account_id,
                      platform_msg_id=body.platform_msg_id, content=body.text, sender="CUSTOMER", status="SENT", created_at=occurred)
        db.add(row)
        conv.is_read = False
        conv.version += 1
        conv.ai_generation += 1
        conv.last_message_at = max(conv.last_message_at or occurred, occurred)
        # AI-01 will schedule/fence model jobs. Until then the seller handles actual incoming messages.
        if conv.ai_status == "AI_HANDLING":
            conv.ai_status = "NEEDS_SELLER"
        await db.flush()
        db.add(RealtimeOutbox(event_type="message:new", data={"conversation_id": conv.id, "message_id": row.id}))
        db.add(RealtimeOutbox(event_type="conversation:updated", data={"conversation_id": conv.id, "version": conv.version}))
        await db.commit()
        return success({"conversation_id": conv.id, "message_id": row.id})
