from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
from sqlalchemy import or_, select

from shared.config import settings
from shared.db.models import ConversationOutbox, Message, RealtimeOutbox
from shared.db.session import get_session_factory
from shared.service_http import internal_request, poll
from shared.auth import AuthError


def message_data(row):
    return {"id": row.id, "conversation_id": row.conversation_id, "sender": row.sender, "content": row.content,
            "status": row.status, "platform_msg_id": row.platform_msg_id, "error_code": row.error_code,
            "delivery_unknown": row.delivery_unknown, "created_at": row.created_at.isoformat() + "Z"}


def changed(db, row):
    db.add(RealtimeOutbox(event_type="message:updated", data={
        "conversation_id": row.conversation_id, "message_id": row.id, "status": row.status,
    }))


async def dispatch_one():
    factory = get_session_factory()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with factory.begin() as db:
        job = await db.scalar(select(ConversationOutbox).where(ConversationOutbox.status == "PENDING",
            or_(ConversationOutbox.next_attempt_at.is_(None), ConversationOutbox.next_attempt_at <= now))
            .order_by(ConversationOutbox.created_at, ConversationOutbox.id).limit(1).with_for_update(skip_locked=True))
        if job is None:
            return False
        row = await db.get(Message, job.message_id, with_for_update=True)
        if row.delivery_unknown:
            row.status, row.error_code = "FAILED", "DELIVERY_UNKNOWN"
            job.status = "FAILED"
            changed(db, row)
            return True
        if row.status != "SENDING":
            job.status = "SENT" if row.status == "SENT" else "FAILED"
            return True
        row.delivery_unknown = True
        row.error_code = "DISPATCH_IN_PROGRESS"
        job.attempt_count += 1
        job.next_attempt_at = now + timedelta(seconds=60)
        message_id, job_id = row.id, job.id
        attempt_id = str(uuid4())
    # The durable unknown marker prevents blind resend after worker/network crashes.
    try:
        result = await internal_request("POST", settings.platform_service_url + f"/internal/messages/{message_id}/dispatch",
                                        body={"attempt_id": attempt_id})
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout):
        result = {"accepted": False, "delivery_unknown": False, "error_code": "CONNECTION_FAILED"}
    except AuthError as exc:
        result = {"accepted": False, "delivery_unknown": exc.code != "CONFIG_REQUIRED", "error_code": exc.code}
    except httpx.HTTPError:
        result = {"accepted": False, "delivery_unknown": True, "error_code": "DELIVERY_UNKNOWN"}
    async with factory.begin() as db:
        job = await db.get(ConversationOutbox, job_id, with_for_update=True)
        row = await db.get(Message, message_id, with_for_update=True)
        row.delivery_unknown = bool(result.get("delivery_unknown", False))
        row.error_code = result.get("error_code")
        if result.get("accepted") and result.get("provider_message_id"):
            row.status, row.error_code, row.delivery_unknown = "SENT", None, False
            row.platform_msg_id = result["provider_message_id"]
            job.status = "SENT"
        elif row.error_code == "CONNECTION_FAILED" and job.attempt_count < 3:
            job.next_attempt_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=5 * job.attempt_count)
        else:
            row.status, job.status = "FAILED", "FAILED"
        changed(db, row)
    return True


async def outgoing_worker():
    await poll(dispatch_one)
