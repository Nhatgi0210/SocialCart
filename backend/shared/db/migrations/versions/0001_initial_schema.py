"""Initial schema — tất cả bảng V1

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-26

Tạo toàn bộ bảng theo models.py:
  users, platform_connections,
  customers, customer_notes,
  conversations, messages, conversation_outbox,
  products, variants,
  orders, order_items, inventory_movements, request_idempotency,
  ai_faqs, ai_config,
  webhook_receipts, webhook_outbox
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── platform_connections ──────────────────────────────────────────────────
    op.create_table(
        "platform_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("platform", sa.Enum("FACEBOOK", "ZALO", name="platform_enum"), nullable=False),
        sa.Column("account_id", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255)),
        sa.Column("encrypted_access_token", sa.Text()),
        sa.Column("encrypted_refresh_token", sa.Text()),
        sa.Column("token_expires_at", sa.DateTime(6)),
        sa.Column(
            "status",
            sa.Enum("CONNECTED", "DISCONNECTED", "ERROR", name="connection_status_enum"),
            nullable=False,
            server_default="DISCONNECTED",
        ),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
        sa.UniqueConstraint("platform", "account_id", name="uq_platform_connection_account"),
    )

    # ── customers ─────────────────────────────────────────────────────────────
    op.create_table(
        "customers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("platform", sa.Enum("FACEBOOK", "ZALO", name="platform_enum2"), nullable=False),
        sa.Column("platform_account_id", sa.String(255), nullable=False),
        sa.Column("platform_user_id", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100)),
        sa.Column("avatar_url", sa.String(1000)),
        sa.Column("phone", sa.String(20)),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
        sa.UniqueConstraint(
            "platform", "platform_account_id", "platform_user_id",
            name="uq_customer_platform",
        ),
    )
    op.create_index(
        "ix_customer_platform_user", "customers",
        ["platform", "platform_account_id", "platform_user_id"],
    )

    # ── customer_notes ────────────────────────────────────────────────────────
    op.create_table(
        "customer_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
    )
    op.create_index("ix_customer_notes_customer_id", "customer_notes", ["customer_id"])

    # ── conversations ─────────────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("platform", sa.Enum("FACEBOOK", "ZALO", name="platform_enum3"), nullable=False),
        sa.Column("platform_account_id", sa.String(255), nullable=False),
        sa.Column("platform_chat_id", sa.String(255), nullable=False),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("NEW", "IN_PROGRESS", "RESOLVED", name="conv_status_enum"),
            nullable=False,
            server_default="NEW",
        ),
        sa.Column(
            "ai_status",
            sa.Enum("AI_HANDLING", "NEEDS_SELLER", "SELLER_HANDLING", name="conv_ai_status_enum"),
            nullable=False,
            server_default="AI_HANDLING",
        ),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ai_generation", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_message_at", sa.DateTime(6)),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
        sa.UniqueConstraint(
            "platform", "platform_account_id", "platform_chat_id",
            name="uq_conversation_platform",
        ),
        sa.CheckConstraint("version >= 1", name="ck_conversation_version_min"),
        sa.CheckConstraint("ai_generation >= 0", name="ck_conversation_ai_generation_min"),
    )
    op.create_index("ix_conversation_customer_id", "conversations", ["customer_id"])
    op.create_index("ix_conversation_last_message_at", "conversations", ["last_message_at"])

    # ── messages ──────────────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(36),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.Enum("FACEBOOK", "ZALO", name="platform_enum4"), nullable=False),
        sa.Column("platform_account_id", sa.String(255), nullable=False),
        sa.Column("platform_msg_id", sa.String(255)),
        sa.Column("sender", sa.Enum("CUSTOMER", "SELLER", "AI", name="msg_sender_enum"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("SENDING", "SENT", "FAILED", name="msg_status_enum"),
            nullable=False,
            server_default="SENT",
        ),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
        sa.UniqueConstraint(
            "platform", "platform_account_id", "platform_msg_id",
            name="uq_message_platform_msg_id",
        ),
        sa.CheckConstraint("length(content) >= 1", name="ck_message_content_nonempty"),
    )
    op.create_index("ix_message_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_message_created_at", "messages", ["created_at"])

    # ── conversation_outbox ───────────────────────────────────────────────────
    op.create_table(
        "conversation_outbox",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("message_id", sa.String(36), sa.ForeignKey("messages.id"), nullable=False, unique=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "SENT", "FAILED", name="outbox_status_enum"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("attempt_count", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(6)),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
    )
    op.create_index("ix_outbox_status_next_attempt", "conversation_outbox", ["status", "next_attempt_at"])

    # ── products ──────────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("image_url", sa.String(1000)),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "INACTIVE", name="product_status_enum"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("deleted_at", sa.DateTime(6)),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
    )
    op.create_index("ix_product_status_deleted", "products", ["status", "deleted_at"])

    # ── variants ──────────────────────────────────────────────────────────────
    op.create_table(
        "variants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("deleted_at", sa.DateTime(6)),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
        sa.CheckConstraint("price >= 1 AND price <= 2147483647", name="ck_variant_price_range"),
        sa.CheckConstraint("stock >= 0", name="ck_variant_stock_nonneg"),
        sa.CheckConstraint("version >= 1", name="ck_variant_version_min"),
    )
    op.create_index("ix_variant_product_id", "variants", ["product_id"])

    # ── orders ────────────────────────────────────────────────────────────────
    op.create_table(
        "orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_code", sa.String(50), nullable=False, unique=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id")),
        sa.Column(
            "status",
            sa.Enum("PENDING", "CONFIRMED", "SHIPPING", "COMPLETED", "CANCELLED", name="order_status_enum"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("total_amount", sa.Integer(), nullable=False),
        sa.Column("shipping_name", sa.String(100)),
        sa.Column("shipping_phone", sa.String(20)),
        sa.Column("shipping_address", sa.String(500)),
        sa.Column("note", sa.Text()),
        sa.Column("created_by", sa.Enum("AI", "SELLER", name="order_creator_enum"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
        sa.CheckConstraint("total_amount >= 0", name="ck_order_total_nonneg"),
        sa.CheckConstraint("version >= 1", name="ck_order_version_min"),
    )
    op.create_index("ix_order_customer_id", "orders", ["customer_id"])
    op.create_index("ix_order_status", "orders", ["status"])
    op.create_index("ix_order_created_at", "orders", ["created_at"])

    # ── order_items ───────────────────────────────────────────────────────────
    op.create_table(
        "order_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_id", sa.String(36), sa.ForeignKey("variants.id"), nullable=False),
        sa.Column("product_name_snapshot", sa.String(100), nullable=False),
        sa.Column("variant_name_snapshot", sa.String(100), nullable=False),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.CheckConstraint("unit_price >= 1", name="ck_order_item_price_pos"),
        sa.CheckConstraint("quantity >= 1 AND quantity <= 1000000", name="ck_order_item_qty_range"),
    )
    op.create_index("ix_order_item_order_id", "order_items", ["order_id"])

    # ── inventory_movements ───────────────────────────────────────────────────
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("variant_id", sa.String(36), sa.ForeignKey("variants.id"), nullable=False),
        sa.Column("movement_type", sa.Enum("DEDUCT", "RESTORE", name="movement_type_enum"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.UniqueConstraint("order_id", "variant_id", "movement_type", name="uq_inventory_movement"),
        sa.CheckConstraint("quantity >= 1", name="ck_inventory_qty_pos"),
    )
    op.create_index("ix_inventory_order_id", "inventory_movements", ["order_id"])

    # ── request_idempotency ───────────────────────────────────────────────────
    op.create_table(
        "request_idempotency",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(36)),
        sa.Column("response_body", sa.Text()),
        sa.Column("expires_at", sa.DateTime(6), nullable=False),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.UniqueConstraint("actor_id", "operation", "key", name="uq_idempotency_actor_op_key"),
    )
    op.create_index("ix_idempotency_expires_at", "request_idempotency", ["expires_at"])

    # ── ai_faqs ───────────────────────────────────────────────────────────────
    op.create_table(
        "ai_faqs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("question", sa.String(500), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
    )

    # ── ai_config ─────────────────────────────────────────────────────────────
    op.create_table(
        "ai_config",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
    )
    op.create_index("ix_ai_config_key", "ai_config", ["key"])

    # ── webhook_receipts ──────────────────────────────────────────────────────
    op.create_table(
        "webhook_receipts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("platform", sa.Enum("FACEBOOK", "ZALO", name="platform_enum5"), nullable=False),
        sa.Column("account_id", sa.String(255), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.UniqueConstraint("platform", "account_id", "event_id", name="uq_webhook_receipt"),
    )
    op.create_index("ix_webhook_receipt_processed", "webhook_receipts", ["processed", "created_at"])

    # ── webhook_outbox ────────────────────────────────────────────────────────
    op.create_table(
        "webhook_outbox",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("platform", sa.Enum("FACEBOOK", "ZALO", name="platform_enum6"), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "SENT", "FAILED", name="webhook_outbox_status_enum"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("attempt_count", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(6)),
        sa.Column("created_at", sa.DateTime(6), nullable=False),
        sa.Column("updated_at", sa.DateTime(6), nullable=False),
    )
    op.create_index("ix_webhook_outbox_status_next", "webhook_outbox", ["status", "next_attempt_at"])


def downgrade() -> None:
    op.drop_table("webhook_outbox")
    op.drop_table("webhook_receipts")
    op.drop_table("ai_config")
    op.drop_table("ai_faqs")
    op.drop_table("request_idempotency")
    op.drop_table("inventory_movements")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("variants")
    op.drop_table("products")
    op.drop_table("conversation_outbox")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("customer_notes")
    op.drop_table("customers")
    op.drop_table("platform_connections")
    op.drop_table("users")

    # Drop enums (MySQL sẽ dọn cùng với table, nhưng explicit cho clarity)
    for enum_name in [
        "platform_enum", "platform_enum2", "platform_enum3", "platform_enum4",
        "platform_enum5", "platform_enum6",
        "connection_status_enum", "conv_status_enum", "conv_ai_status_enum",
        "msg_sender_enum", "msg_status_enum", "outbox_status_enum",
        "product_status_enum", "order_status_enum", "order_creator_enum",
        "movement_type_enum", "webhook_outbox_status_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
