from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException

from app.images import read_image, save_image
from app.schemas import MAX_INT, ProductCreate, ProductStatus, ProductUpdate, VariantInput, VariantUpdate
from shared.auth import AuthError
from shared.db.models import Product, Variant
from shared.inbox_http import DB, Limit, Page, inbox_service, internal_token, paged, success, utc
from shared.product_images import IMAGE_MAX_BYTES, IMAGE_ROUTE

app, seller = inbox_service("product-service")
router = APIRouter(prefix="/api/v1/products", dependencies=[Depends(seller)])


def variant_data(row: Variant):
    return {"id": row.id, "product_id": row.product_id, "name": row.name, "price": row.price,
            "stock": row.stock, "low_stock_threshold": row.low_stock_threshold, "version": row.version}


def product_data(row: Product, variants: list[Variant]):
    variants = sorted(variants, key=lambda variant: (variant.created_at, variant.id))
    return {"id": row.id, "name": row.name, "description": row.description or "", "image_url": row.image_url,
            "status": row.status, "total_stock": sum(variant.stock for variant in variants),
            "variants": [variant_data(variant) for variant in variants], "created_at": utc(row.created_at)}


def check_total(stock: int):
    if stock > MAX_INT:
        raise AuthError(409, "STOCK_LIMIT", "Tổng tồn kho vượt giới hạn cho phép")


async def list_catalog(db, page, limit, filters):
    total = await db.scalar(select(func.count()).select_from(Product).where(*filters))
    rows = await db.scalars(
        select(Product).options(selectinload(Product.variants.and_(Variant.deleted_at.is_(None))))
        .where(*filters).order_by(Product.created_at.desc(), Product.id.desc())
        .offset((page - 1) * limit).limit(limit)
    )
    return paged([product_data(row, row.variants) for row in rows], page, limit, total)


async def get_product_row(db, id, *, lock=False):
    stmt = select(Product).where(Product.id == str(id), Product.deleted_at.is_(None))
    row = await db.scalar(stmt.with_for_update() if lock else stmt)
    if row is None:
        raise AuthError(404, "NOT_FOUND", "Không tìm thấy sản phẩm")
    return row


async def live_variants(db, product, *, lock=False):
    stmt = select(Variant).where(Variant.product_id == product.id, Variant.deleted_at.is_(None)).order_by(Variant.id)
    return list(await db.scalars(stmt.with_for_update() if lock else stmt))


def find_variant(variants, id):
    for variant in variants:
        if variant.id == str(id):
            return variant
    raise AuthError(404, "NOT_FOUND", "Không tìm thấy biến thể")


@app.get(IMAGE_ROUTE + "/{filename}")
async def product_image(filename: str):
    return await run_in_threadpool(read_image, filename)


@router.post("/images", status_code=201, openapi_extra={"requestBody": {
    "required": True, "content": {"multipart/form-data": {"schema": {
        "type": "object", "additionalProperties": False, "required": ["file"],
        "properties": {"file": {"type": "string", "format": "binary"}},
    }}},
}})
async def upload_image(request: Request):
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "multipart/form-data":
        raise AuthError(422, "VALIDATION_ERROR", "Chọn một tệp ảnh")
    try:
        async with request.form(max_files=1, max_fields=0) as form:
            file = form.get("file")
            if not isinstance(file, UploadFile):
                raise AuthError(422, "VALIDATION_ERROR", "Chọn một tệp ảnh")
            content = await file.read(IMAGE_MAX_BYTES + 1)
            url = await run_in_threadpool(save_image, content, file.content_type)
    except HTTPException:
        raise AuthError(422, "VALIDATION_ERROR", "Chỉ gửi một tệp ảnh có tên trường file") from None
    return success({"image_url": url})


@router.get("")
async def list_products(db: DB, page: Page = 1, limit: Limit = 20, status: ProductStatus | None = None,
                        search: Annotated[str | None, Query(max_length=200)] = None, low_stock: bool | None = None):
    filters = [Product.deleted_at.is_(None)]
    if status is not None:
        filters.append(Product.status == status)
    if search and search.strip():
        filters.append(func.lower(Product.name).contains(search.strip().lower(), autoescape=True))
    if low_stock is not None:
        low = Product.variants.any(Variant.deleted_at.is_(None) & (Variant.stock <= Variant.low_stock_threshold))
        filters.append(low if low_stock else ~low)
    return await list_catalog(db, page, limit, filters)


@app.get("/internal/catalog", dependencies=[Depends(internal_token)])
async def catalog(db: DB, page: Page = 1, limit: Limit = 20, active_only: bool = True):
    filters = [Product.deleted_at.is_(None), Product.variants.any(Variant.deleted_at.is_(None))]
    if active_only:
        filters.append(Product.status == "ACTIVE")
    return await list_catalog(db, page, limit, filters)


@router.post("", status_code=201)
async def create_product(body: ProductCreate, db: DB):
    check_total(sum(variant.stock for variant in body.variants))
    product = Product(**body.model_dump(exclude={"variants"}), status="ACTIVE")
    db.add(product)
    await db.flush()
    variants = [Variant(product_id=product.id, **entry.model_dump()) for entry in body.variants]
    db.add_all(variants)
    await db.commit()
    return success(product_data(product, variants))


@router.get("/{id}")
async def get_product(id: UUID, db: DB):
    product = await get_product_row(db, id)
    return success(product_data(product, await live_variants(db, product)))


@router.put("/{id}")
async def update_product(id: UUID, body: ProductUpdate, db: DB):
    product = await get_product_row(db, id, lock=True)
    variants = await live_variants(db, product, lock=True)
    if body.status == "ACTIVE" and not variants:
        raise AuthError(409, "VARIANT_REQUIRED", "Cần ít nhất một biến thể để mở bán")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.commit()
    return success(product_data(product, variants))


@router.delete("/{id}", status_code=204)
async def delete_product(id: UUID, db: DB):
    product = await get_product_row(db, id, lock=True)
    variants = await live_variants(db, product, lock=True)
    deleted = datetime.now(timezone.utc).replace(tzinfo=None)
    product.deleted_at = deleted
    product.status = "INACTIVE"
    for row in variants:
        row.deleted_at = deleted
        row.version += 1
    await db.commit()
    return Response(status_code=204)


@router.post("/{id}/variants", status_code=201)
async def create_variant(id: UUID, body: VariantInput, db: DB):
    product = await get_product_row(db, id, lock=True)
    variants = await live_variants(db, product, lock=True)
    check_total(sum(row.stock for row in variants) + body.stock)
    row = Variant(product_id=product.id, **body.model_dump())
    db.add(row)
    await db.commit()
    return success(variant_data(row))


@router.put("/{id}/variants/{variant_id}")
async def update_variant(id: UUID, variant_id: UUID, body: VariantUpdate, db: DB):
    product = await get_product_row(db, id, lock=True)
    variants = await live_variants(db, product, lock=True)
    row = find_variant(variants, variant_id)
    if row.version != body.expected_version:
        raise AuthError(409, "VERSION_CONFLICT", "Biến thể đã thay đổi. Hãy tải lại dữ liệu.")
    if body.stock is not None:
        check_total(sum(variant.stock for variant in variants) - row.stock + body.stock)
    edits = body.model_dump(exclude_unset=True, exclude={"expected_version"})
    if any(getattr(row, field) != value for field, value in edits.items()):
        for field, value in edits.items():
            setattr(row, field, value)
        row.version += 1
    await db.commit()
    return success(variant_data(row))


@router.delete("/{id}/variants/{variant_id}", status_code=204)
async def delete_variant(id: UUID, variant_id: UUID, db: DB):
    product = await get_product_row(db, id, lock=True)
    variants = await live_variants(db, product, lock=True)
    row = find_variant(variants, variant_id)
    row.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    row.version += 1
    if len(variants) == 1:
        product.status = "INACTIVE"
    await db.commit()
    return Response(status_code=204)


app.include_router(router)
