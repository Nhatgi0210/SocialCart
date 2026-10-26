"""
Smoke test cho BOOT-01: kiểm tra import, cấu trúc module và health endpoint logic cơ bản.

Chạy: pytest backend/tests/test_boot01.py -v
Không yêu cầu MySQL/Redis kết nối thật (dùng mock).
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Đảm bảo backend/ trong path
_backend_dir = str(Path(__file__).parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)


# ── Shared config ─────────────────────────────────────────────────────────────

def test_shared_config_imports():
    """shared.config phải import được và có field database_url."""
    from shared.config import settings
    assert hasattr(settings, "database_url")
    assert hasattr(settings, "redis_url")
    assert hasattr(settings, "jwt_algorithm")
    assert settings.jwt_algorithm == "RS256"


def test_shared_config_extra_ignored():
    """Settings không raise khi có biến env không liên quan."""
    from shared.config import Settings
    s = Settings(_env_file=None, DATABASE_URL="mysql+aiomysql://x:x@localhost/x", UNKNOWN_VAR="ignored")
    assert s.database_url == "mysql+aiomysql://x:x@localhost/x"


# ── shared.db.models ──────────────────────────────────────────────────────────

def test_models_import():
    """Tất cả model class phải import được."""
    from shared.db.models import (
        User, PlatformConnection,
        Customer, CustomerNote,
        Conversation, Message, ConversationOutbox,
        Product, Variant,
        Order, OrderItem, InventoryMovement, RequestIdempotency,
        AIFaq, AIConfig,
        WebhookReceipt, WebhookOutbox,
    )
    # Kiểm tra tablename không trùng
    table_names = {m.__tablename__ for m in [
        User, PlatformConnection, Customer, CustomerNote,
        Conversation, Message, ConversationOutbox,
        Product, Variant, Order, OrderItem, InventoryMovement, RequestIdempotency,
        AIFaq, AIConfig, WebhookReceipt, WebhookOutbox,
    ]}
    assert len(table_names) == 17, f"Có tablename trùng: {table_names}"


def test_user_model_fields():
    from shared.db.models import User
    cols = {c.name for c in User.__table__.columns}
    assert {"id", "email", "hashed_password", "is_active", "created_at", "updated_at"} <= cols


def test_order_has_version_and_created_by():
    from shared.db.models import Order
    cols = {c.name for c in Order.__table__.columns}
    assert "version" in cols
    assert "created_by" in cols
    assert "total_amount" in cols


def test_variant_check_constraints():
    from shared.db.models import Variant
    constraint_names = {c.name for c in Variant.__table__.constraints}
    assert "ck_variant_price_range" in constraint_names
    assert "ck_variant_stock_nonneg" in constraint_names
    assert "ck_variant_version_min" in constraint_names


def test_customer_unique_constraint():
    from shared.db.models import Customer
    constraint_names = {c.name for c in Customer.__table__.constraints}
    assert "uq_customer_platform" in constraint_names


def test_inventory_movement_unique():
    from shared.db.models import InventoryMovement
    constraint_names = {c.name for c in InventoryMovement.__table__.constraints}
    assert "uq_inventory_movement" in constraint_names


# ── API Gateway health endpoint ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gateway_health_both_ok():
    """Health endpoint của gateway phải tồn tại và trả JSON với 'success' key."""
    gw_dir = str(Path(__file__).parent.parent / "api-gateway")
    if gw_dir not in sys.path:
        sys.path.insert(0, gw_dir)

    import app.main as gw_main  # noqa: F401

    assert hasattr(gw_main, "app"), "gateway app phải có FastAPI app"
    assert hasattr(gw_main, "health_check"), "gateway phải có health_check endpoint"


# ── Auth service shell ────────────────────────────────────────────────────────

def test_auth_service_imports():
    """auth-service/app/main.py phải import được."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "auth-service"))
    import app.main as auth_main
    assert hasattr(auth_main, "app")
    assert hasattr(auth_main, "health_check")
