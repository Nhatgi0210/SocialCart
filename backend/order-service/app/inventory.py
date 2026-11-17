from collections import defaultdict

from sqlalchemy import select

from app.schemas import MAX_INT, MAX_QUANTITY
from shared.auth import AuthError
from shared.db.models import InventoryMovement, OrderItem, Product, Variant


async def lock_catalog(db, variant_ids):
    # Product service takes product locks before variant locks. Parent IDs are immutable.
    parent_ids = select(Variant.product_id).where(Variant.id.in_(variant_ids))
    products = {row.id: row for row in await db.scalars(
        select(Product).where(Product.id.in_(parent_ids)).order_by(Product.id).with_for_update()
    )}
    variants = {row.id: row for row in await db.scalars(
        select(Variant).where(Variant.id.in_(variant_ids)).order_by(Variant.id).with_for_update()
    )}
    return products, variants


def available(variant_id, quantity, products, variants):
    variant = variants.get(variant_id)
    product = products.get(variant.product_id) if variant is not None else None
    if product is None or product.status != "ACTIVE" or product.deleted_at or variant.deleted_at:
        raise AuthError(409, "VARIANT_UNAVAILABLE", "Sản phẩm hoặc biến thể đã ngừng bán")
    if variant.stock < quantity:
        raise AuthError(409, "INSUFFICIENT_STOCK", f"Không đủ tồn kho cho {product.name} · {variant.name}")
    return product, variant


async def save_items(db, order, requested, existing):
    quantities = defaultdict(int)
    for item in requested:
        variant_id = str(item.variant_id)
        quantities[variant_id] += item.quantity
        if quantities[variant_id] > MAX_QUANTITY:
            raise AuthError(422, "VALIDATION_ERROR", "Số lượng mỗi biến thể vượt giới hạn")
    products, variants = await lock_catalog(db, list(quantities))
    old_items = {row.variant_id: row for row in existing}
    result = []
    for variant_id, quantity in quantities.items():
        product, variant = available(variant_id, quantity, products, variants)
        row = old_items.pop(variant_id, None)
        if row is None:
            row = OrderItem(order_id=order.id, variant_id=variant_id, product_name_snapshot=product.name,
                            variant_name_snapshot=variant.name, unit_price=variant.price, quantity=quantity)
            db.add(row)
        row.quantity = quantity
        result.append(row)
    total = sum(row.quantity * row.unit_price for row in result)
    if total > MAX_INT:
        raise AuthError(422, "VALIDATION_ERROR", "Tổng tiền vượt giới hạn")
    order.total_amount = total
    for row in old_items.values():
        await db.delete(row)
    return result


async def deduct_stock(db, order, items):
    if not items:
        raise AuthError(409, "INVALID_TRANSITION", "Đơn chưa có sản phẩm")
    products, variants = await lock_catalog(db, [item.variant_id for item in items])
    for row in items:
        _, variant = available(row.variant_id, row.quantity, products, variants)
        variant.stock -= row.quantity
        variant.version += 1
        db.add(InventoryMovement(order_id=order.id, variant_id=variant.id,
                                 movement_type="DEDUCT", quantity=row.quantity))


async def restore_stock(db, order):
    deductions = list(await db.scalars(
        select(InventoryMovement).where(InventoryMovement.order_id == order.id,
                                         InventoryMovement.movement_type == "DEDUCT")
    ))
    if not deductions:
        raise AuthError(409, "INVALID_TRANSITION", "Đơn chưa có dữ liệu trừ kho để hoàn")
    products, variants = await lock_catalog(db, [row.variant_id for row in deductions])
    live = await db.scalars(select(Variant).where(Variant.product_id.in_(products),
                                                  Variant.deleted_at.is_(None)).order_by(Variant.id).with_for_update())
    totals = defaultdict(int)
    for variant in live:
        totals[variant.product_id] += variant.stock
    for row in deductions:
        variant = variants[row.variant_id]
        if variant.deleted_at is None:
            totals[variant.product_id] += row.quantity
        if variant.stock + row.quantity > MAX_INT or totals[variant.product_id] > MAX_INT:
            raise AuthError(409, "STOCK_LIMIT", "Hoàn kho vượt giới hạn tồn kho")
        variant.stock += row.quantity
        variant.version += 1
        db.add(InventoryMovement(order_id=order.id, variant_id=variant.id,
                                 movement_type="RESTORE", quantity=row.quantity))
