"""
ORM models tập trung cho toàn bộ SocialCart V1.

Quy ước:
- ID: UUID chuỗi 36 ký tự, default=uuid4
- Tiền: Integer VNĐ (không DECIMAL/FLOAT)
- Timestamp: DATETIME(6) UTC, không timezone-aware type
- Xóa mềm: deleted_at nullable
- version: tăng khi cần optimistic lock
- Không tạo bảng qua create_all; dùng Alembic migration
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    from datetime import timezone
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


# ─────────────────────────── AUTH ────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        Index("ix_users_email", "email"),
    )


# ─────────────────────────── PLATFORM ────────────────────────────────────────

class PlatformConnection(Base):
    __tablename__ = "platform_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(Enum("FACEBOOK", "ZALO", name="platform_enum"), nullable=False)
    account_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Page ID / OA ID
    display_name: Mapped[str | None] = mapped_column(String(255))
    # Token mã hóa AES-256-GCM, không trả về UI
    encrypted_access_token: Mapped[str | None] = mapped_column(Text)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(6))
    status: Mapped[str] = mapped_column(
        Enum("CONNECTED", "DISCONNECTED", "ERROR", name="connection_status_enum"),
        default="DISCONNECTED",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("platform", "account_id", name="uq_platform_connection_account"),
    )


# ─────────────────────────── CUSTOMER ────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(Enum("FACEBOOK", "ZALO", name="platform_enum2"), nullable=False)
    platform_account_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Page/OA ID
    platform_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(1000))
    phone: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    notes: Mapped[list[CustomerNote]] = relationship("CustomerNote", back_populates="customer", lazy="select")

    __table_args__ = (
        UniqueConstraint("platform", "platform_account_id", "platform_user_id", name="uq_customer_platform"),
        Index("ix_customer_platform_user", "platform", "platform_account_id", "platform_user_id"),
    )


class CustomerNote(Base):
    __tablename__ = "customer_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    customer: Mapped[Customer] = relationship("Customer", back_populates="notes")

    __table_args__ = (
        Index("ix_customer_notes_customer_id", "customer_id"),
    )


# ─────────────────────────── CONVERSATION ────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(Enum("FACEBOOK", "ZALO", name="platform_enum3"), nullable=False)
    platform_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_chat_id: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("NEW", "IN_PROGRESS", "RESOLVED", name="conv_status_enum"),
        default="NEW", nullable=False,
    )
    ai_status: Mapped[str] = mapped_column(
        Enum("AI_HANDLING", "NEEDS_SELLER", "SELLER_HANDLING", name="conv_ai_status_enum"),
        default="AI_HANDLING", nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ai_generation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(6))
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    messages: Mapped[list[Message]] = relationship("Message", back_populates="conversation", lazy="select")

    __table_args__ = (
        UniqueConstraint("platform", "platform_account_id", "platform_chat_id", name="uq_conversation_platform"),
        CheckConstraint("version >= 1", name="ck_conversation_version_min"),
        CheckConstraint("ai_generation >= 0", name="ck_conversation_ai_generation_min"),
        Index("ix_conversation_customer_id", "customer_id"),
        Index("ix_conversation_last_message_at", "last_message_at"),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(Enum("FACEBOOK", "ZALO", name="platform_enum4"), nullable=False)
    platform_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_msg_id: Mapped[str | None] = mapped_column(String(255))  # nullable cho message SELLER/AI outgoing
    sender: Mapped[str] = mapped_column(
        Enum("CUSTOMER", "SELLER", "AI", name="msg_sender_enum"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("SENDING", "SENT", "FAILED", name="msg_status_enum"),
        default="SENT", nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        # Chống duplicate incoming message
        UniqueConstraint(
            "platform", "platform_account_id", "platform_msg_id",
            name="uq_message_platform_msg_id",
        ),
        CheckConstraint("length(content) >= 1", name="ck_message_content_nonempty"),
        Index("ix_message_conversation_id", "conversation_id"),
        Index("ix_message_created_at", "created_at"),
    )


class ConversationOutbox(Base):
    """Outbox bền vững cho outgoing message; worker dispatch đến platform."""
    __tablename__ = "conversation_outbox"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("messages.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        Enum("PENDING", "SENT", "FAILED", name="outbox_status_enum"),
        default="PENDING", nullable=False,
    )
    attempt_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(6))
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        Index("ix_outbox_status_next_attempt", "status", "next_attempt_at"),
    )


# ─────────────────────────── PRODUCT ─────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(
        Enum("ACTIVE", "INACTIVE", name="product_status_enum"),
        default="ACTIVE", nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(6))
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    variants: Mapped[list[Variant]] = relationship("Variant", back_populates="product", lazy="select")

    __table_args__ = (
        Index("ix_product_status_deleted", "status", "deleted_at"),
    )


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)       # VNĐ nguyên
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(6))
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    product: Mapped[Product] = relationship("Product", back_populates="variants")

    __table_args__ = (
        CheckConstraint("price >= 1 AND price <= 2147483647", name="ck_variant_price_range"),
        CheckConstraint("stock >= 0", name="ck_variant_stock_nonneg"),
        CheckConstraint("version >= 1", name="ck_variant_version_min"),
        Index("ix_variant_product_id", "product_id"),
    )


# ─────────────────────────── ORDER ───────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    order_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)
    conversation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("conversations.id"))
    status: Mapped[str] = mapped_column(
        Enum("PENDING", "CONFIRMED", "SHIPPING", "COMPLETED", "CANCELLED", name="order_status_enum"),
        default="PENDING", nullable=False,
    )
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # VNĐ
    shipping_name: Mapped[str | None] = mapped_column(String(100))
    shipping_phone: Mapped[str | None] = mapped_column(String(20))
    shipping_address: Mapped[str | None] = mapped_column(String(500))
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(Enum("AI", "SELLER", name="order_creator_enum"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    items: Mapped[list[OrderItem]] = relationship("OrderItem", back_populates="order", lazy="select")

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_order_total_nonneg"),
        CheckConstraint("version >= 1", name="ck_order_version_min"),
        Index("ix_order_customer_id", "customer_id"),
        Index("ix_order_status", "status"),
        Index("ix_order_created_at", "created_at"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[str] = mapped_column(String(36), ForeignKey("variants.id"), nullable=False)
    # Snapshot tên/giá tại thời điểm tạo đơn
    product_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    variant_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)   # VNĐ snapshot
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped[Order] = relationship("Order", back_populates="items")

    __table_args__ = (
        CheckConstraint("unit_price >= 1", name="ck_order_item_price_pos"),
        CheckConstraint("quantity >= 1 AND quantity <= 1000000", name="ck_order_item_qty_range"),
        Index("ix_order_item_order_id", "order_id"),
    )


class InventoryMovement(Base):
    """Ledger ghi từng lần trừ/hoàn kho theo đơn hàng."""
    __tablename__ = "inventory_movements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False)
    variant_id: Mapped[str] = mapped_column(String(36), ForeignKey("variants.id"), nullable=False)
    movement_type: Mapped[str] = mapped_column(
        Enum("DEDUCT", "RESTORE", name="movement_type_enum"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("order_id", "variant_id", "movement_type", name="uq_inventory_movement"),
        CheckConstraint("quantity >= 1", name="ck_inventory_qty_pos"),
        Index("ix_inventory_order_id", "order_id"),
    )


class RequestIdempotency(Base):
    """Cache kết quả idempotent cho mutation API."""
    __tablename__ = "request_idempotency"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False)    # user_id / worker_id
    operation: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "order.create"
    key: Mapped[str] = mapped_column(String(255), nullable=False)        # client-supplied key
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36))
    response_body: Mapped[str | None] = mapped_column(Text)              # JSON của response
    expires_at: Mapped[datetime] = mapped_column(DateTime(6), nullable=False)  # TTL >= 24h
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("actor_id", "operation", "key", name="uq_idempotency_actor_op_key"),
        Index("ix_idempotency_expires_at", "expires_at"),
    )


# ─────────────────────────── AI ──────────────────────────────────────────────

class AIFaq(Base):
    __tablename__ = "ai_faqs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)


class AIConfig(Base):
    """Cấu hình AI: payment template, collection timeout, v.v."""
    __tablename__ = "ai_config"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        Index("ix_ai_config_key", "key"),
    )


# ─────────────────────────── WEBHOOK ─────────────────────────────────────────

class WebhookReceipt(Base):
    """Bền vững receipt webhook, dùng để dedup incoming event."""
    __tablename__ = "webhook_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(Enum("FACEBOOK", "ZALO", name="platform_enum5"), nullable=False)
    account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("platform", "account_id", "event_id", name="uq_webhook_receipt"),
        Index("ix_webhook_receipt_processed", "processed", "created_at"),
    )


class WebhookOutbox(Base):
    """Outbox cho outgoing webhook từ system sang platform (nếu cần)."""
    __tablename__ = "webhook_outbox"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(Enum("FACEBOOK", "ZALO", name="platform_enum6"), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("PENDING", "SENT", "FAILED", name="webhook_outbox_status_enum"),
        default="PENDING", nullable=False,
    )
    attempt_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(6))
    created_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        Index("ix_webhook_outbox_status_next", "status", "next_attempt_at"),
    )
