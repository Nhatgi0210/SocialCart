from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.idempotency import run_mutation
from app.inventory import deduct_stock, restore_stock, save_items
from app.schemas import ChangeStatus, CreateOrder, EditOrder, OrderStatus
from shared.auth import AuthError
from shared.db.models import Conversation, Order, OrderItem, RealtimeOutbox
from shared.inbox_http import DB, Limit, Page, inbox_service, paged, success, utc

app, seller = inbox_service("order-service")
router = APIRouter(prefix="/api/v1/orders", dependencies=[Depends(seller)])
Seller = Annotated[dict, Depends(seller)]
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=100)]
SHIPPING_FIELDS = {"customer_name": "shipping_name", "phone_number": "shipping_phone", "address": "shipping_address"}
NEXT_STATUS = {
    "PENDING": {"CONFIRMED", "CANCELLED"}, "CONFIRMED": {"SHIPPING", "CANCELLED"},
    "SHIPPING": {"COMPLETED", "CANCELLED"},
}


def order_data(order, items):
    return {
        "id": order.id, "order_code": order.order_code, "conversation_id": order.conversation_id,
        "customer_id": order.customer_id, "status": order.status, "created_by": order.created_by,
        "customer_name": order.shipping_name, "phone_number": order.shipping_phone,
        "address": order.shipping_address, "note": order.note or "", "total_amount": order.total_amount,
        "version": order.version, "created_at": utc(order.created_at), "updated_at": utc(order.updated_at),
        "items": [
            {"id": item.id, "variant_id": item.variant_id, "product_name": item.product_name_snapshot,
             "variant_name": item.variant_name_snapshot, "unit_price": item.unit_price,
             "quantity": item.quantity, "subtotal": item.unit_price * item.quantity}
            for item in sorted(items, key=lambda item: item.id)
        ],
    }


async def find_order(db, id, *, lock=False):
    statement = select(Order).where(Order.id == str(id))
    order = await db.scalar(statement.with_for_update() if lock else statement.options(selectinload(Order.items)))
    if order is None:
        raise AuthError(404, "NOT_FOUND", "Không tìm thấy đơn hàng")
    return order


def check_version(order, expected):
    if order.version != expected:
        raise AuthError(409, "VERSION_CONFLICT", "Đơn đã thay đổi. Vui lòng tải lại trước khi thao tác")


def queue_event(db, order, kind):
    if order.conversation_id is not None:
        db.add(RealtimeOutbox(event_type=kind, data={
            "order_id": order.id, "conversation_id": order.conversation_id, "version": order.version,
        }))


@router.get("")
async def list_orders(db: DB, page: Page = 1, limit: Limit = 20, status: OrderStatus | None = None,
                      customer_id: UUID | None = None, conversation_id: UUID | None = None):
    filters = []
    for column, value in ((Order.status, status), (Order.customer_id, customer_id),
                          (Order.conversation_id, conversation_id)):
        if value is not None:
            filters.append(column == str(value))
    total = await db.scalar(select(func.count()).select_from(Order).where(*filters))
    rows = await db.scalars(select(Order).options(selectinload(Order.items)).where(*filters)
                            .order_by(Order.created_at.desc(), Order.id.desc())
                            .offset((page - 1) * limit).limit(limit))
    return paged([order_data(row, row.items) for row in rows], page, limit, total)


@router.get("/{id}")
async def get_order(id: UUID, db: DB):
    order = await find_order(db, id)
    return success(order_data(order, order.items))


@router.post("", status_code=201)
async def create_order(body: CreateOrder, key: Key, actor: Seller, db: DB):
    async def mutate():
        conversation = await db.get(Conversation, str(body.conversation_id))
        if conversation is None or conversation.customer_id != str(body.customer_id):
            raise AuthError(422, "VALIDATION_ERROR", "Hội thoại không thuộc khách hàng đã chọn")
        id = uuid4()
        order = Order(id=str(id), order_code="DH-" + id.hex.upper(), customer_id=conversation.customer_id,
                      conversation_id=conversation.id, shipping_name=body.customer_name,
                      shipping_phone=body.phone_number, shipping_address=body.address, note=body.note, created_by="SELLER")
        items = await save_items(db, order, body.items, [])
        db.add(order)
        await db.flush([order])
        await db.flush()
        queue_event(db, order, "order:created")
        return success(order_data(order, items))

    return await run_mutation(db, actor["sub"], "order.create", key, body.model_dump(mode="json"), mutate)


@router.patch("/{id}")
async def edit_order(id: UUID, body: EditOrder, key: Key, actor: Seller, db: DB):
    async def mutate():
        order = await find_order(db, id, lock=True)
        check_version(order, body.expected_version)
        if order.status != "PENDING":
            raise AuthError(409, "INVALID_TRANSITION", "Chỉ sửa nội dung đơn chờ xác nhận")
        items = list(await db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)))
        for field in body.model_fields_set - {"items", "expected_version"}:
            setattr(order, SHIPPING_FIELDS.get(field, field), getattr(body, field))
        if body.items is not None:
            items = await save_items(db, order, body.items, items)
        order.version += 1
        await db.flush()
        queue_event(db, order, "order:updated")
        return success(order_data(order, items))

    request = {"id": str(id), "body": body.model_dump(mode="json", exclude_unset=True)}
    return await run_mutation(db, actor["sub"], "order.edit", key, request, mutate)


@router.patch("/{id}/status")
async def change_status(id: UUID, body: ChangeStatus, key: Key, actor: Seller, db: DB):
    async def mutate():
        order = await find_order(db, id, lock=True)
        check_version(order, body.expected_version)
        if body.status not in NEXT_STATUS.get(order.status, ()):
            raise AuthError(409, "INVALID_TRANSITION", "Không thể chuyển sang trạng thái này")
        items = list(await db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)))
        if body.status == "CONFIRMED":
            await deduct_stock(db, order, items)
        elif body.status == "CANCELLED" and order.status in ("CONFIRMED", "SHIPPING"):
            await restore_stock(db, order)
        order.status = body.status
        order.version += 1
        await db.flush()
        queue_event(db, order, "order:updated")
        return success(order_data(order, items))

    request = {"id": str(id), "body": body.model_dump(mode="json")}
    return await run_mutation(db, actor["sub"], "order.status", key, request, mutate)


app.include_router(router)
