import json
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import or_, select

from shared.auth import AuthError
from shared.config import settings
from shared.db.models import PlatformConnection, WebhookOutbox, WebhookReceipt
from shared.db.session import get_session_factory
from shared.service_http import internal_request, poll


async def deliver_one():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with get_session_factory().begin() as db:
        job = await db.scalar(select(WebhookOutbox).where(WebhookOutbox.status == "PENDING",
            or_(WebhookOutbox.next_attempt_at.is_(None), WebhookOutbox.next_attempt_at <= now))
            .order_by(WebhookOutbox.created_at, WebhookOutbox.id).limit(1).with_for_update(skip_locked=True))
        if job is None:
            return False
        data = json.loads(job.payload)
        try:
            connection = await db.scalar(select(PlatformConnection).where(PlatformConnection.platform == job.platform,
                PlatformConnection.account_id == data["account_id"], PlatformConnection.status == "CONNECTED"))
            if connection is None:
                raise AuthError(503, "PLATFORM_DISCONNECTED", "Nền tảng chưa được kết nối")
            customer = await internal_request("POST", settings.customer_service_url + "/internal/customers/upsert", body={
                "platform": job.platform, "platform_account_id": data["account_id"], "platform_user_id": data["user_id"],
            })
            await internal_request("POST", settings.conversation_service_url + "/internal/incoming-messages", body={
                "platform": job.platform, "account_id": data["account_id"], "platform_chat_id": data["user_id"],
                "customer_id": customer["customer"]["id"], "platform_msg_id": data["event_id"],
                "text": data["text"], "occurred_at": data["occurred_at"],
            })
        except (httpx.HTTPError, AuthError):
            job.attempt_count = min(job.attempt_count + 1, 30000)
            job.next_attempt_at = now + timedelta(seconds=min(300, 2 ** min(job.attempt_count, 8)))
            return False
        job.status = "SENT"
        receipt = await db.get(WebhookReceipt, job.receipt_id)
        receipt.processed = True
    return True


async def incoming_worker():
    await poll(deliver_one)
