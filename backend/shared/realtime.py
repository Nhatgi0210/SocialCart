"""Durable invalidation publisher; Redis is only a wake-up signal for API reads."""
import json
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, model_validator
from redis.exceptions import RedisError
from sqlalchemy import or_, select

from shared.db.models import RealtimeOutbox

CHANNEL = "sc:realtime:v1"
EVENT_TYPES = ("message:new", "message:updated", "conversation:updated", "order:created",
               "order:updated", "dashboard:stats:updated", "realtime:resync")


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    event_id: UUID
    occurred_at: datetime
    event_type: Literal[EVENT_TYPES]
    data: dict

    @model_validator(mode="after")
    def validate_data(self):
        required = {
            "message:new": {"conversation_id", "message_id"},
            "message:updated": {"conversation_id", "message_id", "status"},
            "conversation:updated": {"conversation_id", "version"},
            "order:created": {"order_id", "conversation_id", "version"},
            "order:updated": {"order_id", "conversation_id", "version"},
            "dashboard:stats:updated": {"changed_at"}, "realtime:resync": set(),
        }[self.event_type]
        if set(self.data) != required or self.occurred_at.utcoffset() != timezone.utc.utcoffset(None):
            raise ValueError("Invalid event fields or UTC timestamp")
        for key, value in self.data.items():
            if key.endswith("_id") and (not isinstance(value, str) or str(UUID(value)) != value):
                raise ValueError("Invalid UUID")
            if key == "version" and (type(value) is not int or value < 1):
                raise ValueError("Invalid version")
            if key == "status" and value not in ("SENDING", "SENT", "FAILED"):
                raise ValueError("Invalid message status")
            if key == "changed_at":
                if not isinstance(value, str):
                    raise ValueError("Invalid timestamp")
                stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if stamp.utcoffset() != timezone.utc.utcoffset(None):
                    raise ValueError("Invalid timestamp")
        return self


def envelope(event_type, data, *, event_id=None, occurred_at=None):
    stamp = occurred_at or datetime.now(timezone.utc)
    return Event(schema_version=1, event_id=event_id or uuid4(),
                 occurred_at=stamp.replace(tzinfo=timezone.utc), event_type=event_type, data=data).model_dump(mode="json")


async def dispatch_one(factory, redis):
    """Row lock serializes publishers. Failed/crashed publish remains pending.

    A crash after Redis acceptance can redeliver the same event_id. No subscriber
    is required for acceptance: disconnected consumers restore state through HTTP.
    """
    async with factory() as db, db.begin():
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        row = await db.scalar(select(RealtimeOutbox).where(RealtimeOutbox.sent_at.is_(None))
                              .where(or_(RealtimeOutbox.next_attempt_at.is_(None), RealtimeOutbox.next_attempt_at <= now))
                              .order_by(RealtimeOutbox.created_at, RealtimeOutbox.id)
                              .limit(1).with_for_update(skip_locked=True))
        if row is None:
            return False
        event = envelope(row.event_type, row.data, event_id=row.id, occurred_at=row.created_at)
        row.attempt_count += 1
        try:
            await redis.publish(CHANNEL, json.dumps(event))
        except RedisError:
            row.next_attempt_at = now + timedelta(seconds=5)
            return False
        row.sent_at = now
        row.next_attempt_at = None
    return True
