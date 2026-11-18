import asyncio
import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.exc import OperationalError

from shared.auth import AuthError
from shared.db.models import RequestIdempotency


async def run_mutation(db, actor_id, operation, key, request, mutate):
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    for attempt in range(3):
        try:
            return await commit_once(db, actor_id, operation, key, digest, mutate)
        except OperationalError as exc:
            await db.rollback()
            if attempt == 2 or exc.orig.args[0] not in (1205, 1213):
                raise
            await asyncio.sleep(0.05 * (attempt + 1))


async def commit_once(db, actor_id, operation, key, digest, mutate):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(hours=24)
    table = RequestIdempotency
    claim = insert(table).values(actor_id=actor_id, operation=operation, key=key,
                                 request_hash=digest, expires_at=expires_at)
    await db.execute(claim.on_duplicate_key_update(id=table.id))
    row = await db.scalar(select(table).where(table.actor_id == actor_id, table.operation == operation,
                                              table.key == key).with_for_update())
    if row.expires_at > now and row.request_hash != digest:
        raise AuthError(409, "IDEMPOTENCY_CONFLICT", "Mã yêu cầu đã dùng cho nội dung khác")
    if row.expires_at > now and row.response_body is not None:
        response = json.loads(row.response_body)
    else:
        response = await mutate()
        row.request_hash = digest
        row.resource_id = response["data"]["id"]
        row.response_body = json.dumps(response, ensure_ascii=False, separators=(",", ":"))
        row.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)
    await db.commit()
    return response
