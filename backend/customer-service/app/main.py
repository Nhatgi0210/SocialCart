from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert

from shared.auth import AuthError
from shared.db.models import Conversation, Customer, CustomerNote, Order
from shared.inbox_http import DB, Limit, Page, Platform, customer_data, inbox_service, internal_token, paged, success, utc

app, seller = inbox_service("customer-service")
router = APIRouter(prefix="/api/v1/customers", dependencies=[Depends(seller)])


class NoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


class CustomerUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")
    platform: Platform
    platform_account_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
    platform_user_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)] | None = None


def note_data(note: CustomerNote):
    return {"id": note.id, "customer_id": note.customer_id, "content": note.content, "created_at": utc(note.created_at)}


async def find_customer(db: DB, customer_id: UUID):
    customer = await db.get(Customer, str(customer_id))
    if customer is None:
        raise AuthError(404, "NOT_FOUND", "Không tìm thấy khách hàng")
    return customer


@router.get("")
async def list_customers(db: DB, page: Page = 1, limit: Limit = 20, platform: Platform | None = None,
                         search: Annotated[str | None, Query(max_length=100)] = None):
    filters = []
    if platform:
        filters.append(Customer.platform == platform)
    if search and search.strip():
        filters.append(func.lower(Customer.display_name).contains(search.strip().lower(), autoescape=True))
    total = await db.scalar(select(func.count()).select_from(Customer).where(*filters))
    rows = await db.scalars(select(Customer).where(*filters).order_by(Customer.created_at.desc(), Customer.id.desc())
                            .offset((page - 1) * limit).limit(limit))
    return paged([customer_data(row) for row in rows], page, limit, total)


@router.get("/{id}")
async def get_customer(id: UUID, db: DB):
    customer = await find_customer(db, id)
    notes = await db.scalars(select(CustomerNote).where(CustomerNote.customer_id == customer.id)
                             .order_by(CustomerNote.created_at.desc(), CustomerNote.id.desc()))
    conversations = await db.scalars(select(Conversation.id).where(Conversation.customer_id == customer.id)
                                     .order_by(Conversation.last_message_at.desc(), Conversation.id.desc()))
    orders = await db.scalars(select(Order.id).where(Order.customer_id == customer.id)
                              .order_by(Order.created_at.desc(), Order.id.desc()))
    return success({"customer": customer_data(customer), "notes": [note_data(note) for note in notes],
                    "conversation_ids": list(conversations), "order_ids": list(orders)})


@router.post("/{id}/notes", status_code=201)
async def create_note(id: UUID, body: NoteCreate, db: DB):
    customer = await find_customer(db, id)
    note = CustomerNote(customer_id=customer.id, content=body.content)
    db.add(note)
    await db.commit()
    return success(note_data(note))


@router.delete("/{id}/notes/{note_id}", status_code=204)
async def delete_note(id: UUID, note_id: UUID, db: DB):
    note = await db.scalar(select(CustomerNote).where(CustomerNote.id == str(note_id),
                                                       CustomerNote.customer_id == str(id)).with_for_update())
    if note is None:
        raise AuthError(404, "NOT_FOUND", "Không tìm thấy ghi chú")
    await db.delete(note)
    await db.commit()
    return Response(status_code=204)


@app.post("/internal/customers/upsert", dependencies=[Depends(internal_token)])
async def upsert_customer(body: CustomerUpsert, db: DB):
    candidate = str(uuid4())
    identity = body.model_dump(exclude={"name"})
    statement = insert(Customer).values(id=candidate, **identity, display_name=body.name)
    # The unique identity serializes concurrent deliveries of the same customer.
    await db.execute(statement.on_duplicate_key_update(id=Customer.id))
    customer = (await db.scalars(select(Customer).filter_by(**identity).with_for_update())).one()
    if body.name is not None:
        customer.display_name = body.name
    await db.commit()
    return success({"customer": customer_data(customer), "created": customer.id == candidate})


app.include_router(router)
