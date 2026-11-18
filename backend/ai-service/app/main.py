import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert

from shared.auth import AuthError
from shared.db.models import AIConfig, AIFaq
from shared.inbox_http import DB, Limit, Page, inbox_service, internal_token, paged, success

app, seller = inbox_service("ai-service")
router = APIRouter(prefix="/api/v1/ai-config", dependencies=[Depends(seller)])
Text100 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FAQ(Input):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    answer: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
    trigger_keywords: list[Text100] = []


class Bank(Input):
    bank_name: Text100
    account_number: Annotated[str, StringConstraints(pattern=r"^[0-9]+$", max_length=50)]
    account_holder: Text100


class ConfigUpdate(Input):
    order_timeout_seconds: Annotated[int, Field(strict=True, ge=3600, le=259200)] | None = None
    payment_template: Bank | None = None

    @model_validator(mode="after")
    def has_fields(self):
        if not self.model_fields_set or ("order_timeout_seconds" in self.model_fields_set and self.order_timeout_seconds is None):
            raise ValueError("Provide valid settings")
        return self


def faq_data(row):
    return {"id": row.id, "question": row.question, "answer": row.answer, "trigger_keywords": row.trigger_keywords}


async def config_data(db):
    values = {row.key: json.loads(row.value) for row in await db.scalars(
        select(AIConfig).where(AIConfig.key.in_(("order_timeout_seconds", "payment_template")))
    )}
    return {"order_timeout_seconds": values.get("order_timeout_seconds", 86400),
            "payment_template": values.get("payment_template")}


@router.get("")
async def get_config(db: DB):
    return success(await config_data(db))


@router.put("")
async def update_config(body: ConfigUpdate, db: DB):
    for key, value in sorted(body.model_dump(exclude_unset=True).items()):
        stmt = insert(AIConfig).values(key=key, value=json.dumps(value, ensure_ascii=False))
        await db.execute(stmt.on_duplicate_key_update(value=stmt.inserted.value))
    await db.commit()
    return success(await config_data(db))


@router.get("/faqs")
async def list_faqs(db: DB, page: Page = 1, limit: Limit = 20):
    total = await db.scalar(select(func.count()).select_from(AIFaq).where(AIFaq.is_active.is_(True)))
    rows = await db.scalars(select(AIFaq).where(AIFaq.is_active.is_(True))
                            .order_by(AIFaq.created_at.desc(), AIFaq.id).offset((page - 1) * limit).limit(limit))
    return paged([faq_data(row) for row in rows], page, limit, total)


@router.post("/faqs", status_code=201)
async def create_faq(body: FAQ, db: DB):
    row = AIFaq(**body.model_dump())
    db.add(row)
    await db.commit()
    return success(faq_data(row))


async def find_faq(db, id):
    row = await db.scalar(select(AIFaq).where(AIFaq.id == str(id), AIFaq.is_active.is_(True)).with_for_update())
    if row is None:
        raise AuthError(404, "NOT_FOUND", "Không tìm thấy FAQ")
    return row


@router.put("/faqs/{id}")
async def edit_faq(id: UUID, body: FAQ, db: DB):
    row = await find_faq(db, id)
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    await db.commit()
    return success(faq_data(row))


@router.delete("/faqs/{id}", status_code=204)
async def delete_faq(id: UUID, db: DB):
    row = await find_faq(db, id)
    row.is_active = False
    await db.commit()
    return Response(status_code=204)


@app.get("/internal/ai-config", dependencies=[Depends(internal_token)])
async def internal_config(db: DB):
    rows = await db.scalars(select(AIFaq).where(AIFaq.is_active.is_(True)).order_by(AIFaq.id))
    return success({**await config_data(db), "faqs": [faq_data(row) for row in rows]})


app.include_router(router)
