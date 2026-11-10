"""
Smoke test cho BOOT-01: kiểm tra import, cấu trúc module và health endpoint logic cơ bản.

Chạy: pytest backend/tests/test_boot01.py -v
Không yêu cầu MySQL/Redis kết nối thật (dùng mock).
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock

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


def test_duration_settings_from_dotenv(tmp_path):
    from shared.config import Settings
    from pydantic import ValidationError
    path = tmp_path / ".env"
    path.write_text("ACCESS_TOKEN_EXPIRE_MINUTES=15\nREFRESH_TOKEN_EXPIRE_DAYS=7\nSESSION_IDLE_TIMEOUT_SECONDS=86400\n")
    settings = Settings(_env_file=path)
    assert (settings.access_token_expire_minutes, settings.refresh_token_expire_days,
            settings.session_idle_timeout_seconds) == (15, 7, 86400)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ACCESS_TOKEN_EXPIRE_MINUTES="30")


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
    assert {"id", "email", "name", "hashed_password", "is_active", "created_at", "updated_at"} <= cols


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



def test_service_modules_are_distinct():
    from tests.conftest import load_service
    gateway = load_service("api-gateway")
    auth = load_service("auth-service")
    assert gateway is not auth
    assert gateway.app is not auth.app
    assert gateway.app.title == "SocialCart API Gateway"
    assert auth.app.title == "SocialCart Auth Service"


@pytest.mark.asyncio
@pytest.mark.parametrize("service", ["api-gateway", "auth-service"])
@pytest.mark.parametrize("db_ok,redis_ok,status", [(True, True, 200), (False, True, 503), (True, False, 503), (False, False, 503)])
async def test_health_contract(service, db_ok, redis_ok, status, monkeypatch):
    from tests.conftest import load_service
    from shared import health
    from unittest.mock import MagicMock
    import json
    module = load_service(service)
    conn = AsyncMock()
    engine = MagicMock()
    engine.connect.return_value.__aenter__.return_value = conn
    if not db_ok:
        conn.execute.side_effect = RuntimeError("secret DSN")
    redis = AsyncMock()
    if not redis_ok:
        redis.ping.side_effect = RuntimeError("secret Redis")
    monkeypatch.setattr(health, "get_engine", lambda: engine)
    monkeypatch.setattr(module, "get_redis", lambda: redis)
    response = await module.health_check()
    assert response.status_code == status
    body = json.loads(response.body)
    if status == 200:
        assert body["status"] == "ok" and body["service"] == service
        assert body["checked_at"].endswith("Z")
    else:
        assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "secret" not in response.body.decode()


def test_migration_sql_compiles_from_root():
    """Offline compilation catches Windows encoding/import failures, not DB compatibility."""
    import subprocess
    result = subprocess.run([sys.executable, "-X", "utf8", "-m", "alembic", "-c",
                             "backend/shared/db/alembic.ini", "upgrade", "head", "--sql"],
                            cwd=Path(__file__).resolve().parents[2], capture_output=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert "ALTER TABLE users ADD COLUMN name" in result.stdout
    assert "0002_user_name" in result.stdout
