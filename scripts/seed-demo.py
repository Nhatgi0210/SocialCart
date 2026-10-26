"""
scripts/seed-demo.py — Seed dữ liệu demo cho local development.

Dùng: python scripts/seed-demo.py --seller-only
       python scripts/seed-demo.py --all   (thêm catalog/conversation demo)

Idempotent: chạy nhiều lần không tạo duplicate.
Không print mật khẩu ra console.
Không dùng cho môi trường production.
Chỉ tạo dữ liệu local/demo; không gửi tin đến khách thật.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Thêm backend/ vào path
_backend_dir = str(Path(__file__).parent.parent / "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)


async def seed_seller(session) -> None:
    """Tạo user người bán từ env SEED_SELLER_EMAIL / SEED_SELLER_PASSWORD.
    Idempotent: nếu email đã tồn tại, bỏ qua.
    """
    try:
        from passlib.context import CryptContext
    except ImportError:
        print("ERROR: Cần cài passlib[bcrypt]. Chạy: pip install passlib[bcrypt]")
        sys.exit(1)

    from sqlalchemy import select
    from shared.db.models import User

    email = os.environ.get("SEED_SELLER_EMAIL", "").strip()
    password = os.environ.get("SEED_SELLER_PASSWORD", "").strip()

    if not email:
        print("ERROR: SEED_SELLER_EMAIL chưa được đặt trong .env")
        sys.exit(1)
    if not password:
        print("ERROR: SEED_SELLER_PASSWORD chưa được đặt trong .env")
        sys.exit(1)
    if len(password) < 8:
        print("ERROR: SEED_SELLER_PASSWORD phải có ít nhất 8 ký tự")
        sys.exit(1)

    # Kiểm tra tồn tại
    result = await session.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        print(f"INFO: Người bán '{email}' đã tồn tại — bỏ qua.")
        return

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash(password)

    import uuid
    from datetime import datetime, timezone

    user = User(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hashed,
        is_active=True,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(user)
    await session.commit()
    print(f"OK: Đã tạo người bán '{email}'.")


async def seed_demo_catalog(session) -> None:
    """Seed catalog demo — chỉ cho local/test."""
    from sqlalchemy import select
    from shared.db.models import Product, Variant
    import uuid
    from datetime import datetime, timezone

    _now = lambda: datetime.now(timezone.utc).replace(tzinfo=None)

    # Kiểm tra đã có dữ liệu chưa
    result = await session.execute(select(Product).limit(1))
    if result.scalar_one_or_none():
        print("INFO: Catalog demo đã có — bỏ qua.")
        return

    products = [
        {
            "name": "Áo thun basic",
            "description": "Áo thun cotton 100%, nhiều màu sắc",
            "variants": [
                {"name": "S - Trắng", "price": 150_000, "stock": 50},
                {"name": "M - Trắng", "price": 150_000, "stock": 30},
                {"name": "L - Đen", "price": 150_000, "stock": 20},
            ],
        },
        {
            "name": "Quần jean slim fit",
            "description": "Quần jean denim cao cấp",
            "variants": [
                {"name": "28 - Xanh nhạt", "price": 350_000, "stock": 15},
                {"name": "30 - Xanh nhạt", "price": 350_000, "stock": 10},
                {"name": "32 - Đen", "price": 360_000, "stock": 5},
            ],
        },
    ]

    for p_data in products:
        product = Product(
            id=str(uuid.uuid4()),
            name=p_data["name"],
            description=p_data.get("description"),
            status="ACTIVE",
            created_at=_now(),
            updated_at=_now(),
        )
        session.add(product)
        await session.flush()

        for v_data in p_data["variants"]:
            variant = Variant(
                id=str(uuid.uuid4()),
                product_id=product.id,
                name=v_data["name"],
                price=v_data["price"],
                stock=v_data["stock"],
                version=1,
                created_at=_now(),
                updated_at=_now(),
            )
            session.add(variant)

    await session.commit()
    print("OK: Đã seed catalog demo (2 sản phẩm, 6 variants).")


async def main(args: argparse.Namespace) -> None:
    # Load .env
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(_env_path, override=False)
        except ImportError:
            # dotenv không cần thiết nếu env đã được set
            pass

    from shared.db.session import get_session_factory, get_engine

    # Đảm bảo engine tạo trước
    get_engine()
    factory = get_session_factory()

    async with factory() as session:
        await seed_seller(session)
        if args.all:
            await seed_demo_catalog(session)

    print("Seed hoàn tất.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed dữ liệu demo SocialCart")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--seller-only", action="store_true", help="Chỉ tạo tài khoản người bán")
    group.add_argument("--all", action="store_true", help="Tạo người bán + catalog demo")
    parsed = parser.parse_args()
    asyncio.run(main(parsed))
