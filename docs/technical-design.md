# Technical Design Document: SocialCart

> **Trạng thái:** Approved — Đã xác nhận tech stack  
> **Phiên bản:** 1.1  
> **Ngày tạo:** 2026-09-15  
> **Nguồn:** PRD v1.0 + Feature Specification v1.0 + Quyết định tech stack người dùng  
> **Tham chiếu:** [product-requirements.md](./product-requirements.md) · [feature-specification.md](./feature-specification.md)

---

## Mục lục

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Tech Stack — Đã phê duyệt](#2-tech-stack--đã-phê-duyệt)
3. [Cấu trúc thư mục dự án](#3-cấu-trúc-thư-mục-dự-án)
4. [Database Design (MySQL + SQLAlchemy)](#4-database-design-mysql--sqlalchemy)
5. [Backend Design (FastAPI — Services)](#5-backend-design-fastapi--services)
6. [Frontend Design (React + MUI)](#6-frontend-design-react--mui)
7. [AI Chatbot Design (Gemini 1.5 Pro)](#7-ai-chatbot-design-gemini-15-pro)
8. [Tích hợp nền tảng](#8-tích-hợp-nền-tảng)
9. [Realtime & Job Queue](#9-realtime--job-queue)
10. [Authentication (JWT)](#10-authentication-jwt)
11. [File Storage](#11-file-storage)
12. [Environment & Configuration](#12-environment--configuration)
13. [Deployment (Local + ngrok)](#13-deployment-local--ngrok)
14. [Rủi ro kỹ thuật & Mitigation](#14-rủi-ro-kỹ-thuật--mitigation)

---

## 1. Tổng quan kiến trúc

### 1.1. Kiến trúc: Microservices

Người dùng đã chọn **Microservices** — mỗi domain chạy như một service độc lập, giao tiếp qua HTTP (REST) hoặc message queue nội bộ.

> [!IMPORTANT]
> **Lưu ý về độ phức tạp:** Microservices tăng overhead so với Monolith. Để kiểm soát độ phức tạp ở MVP, các services sẽ dùng **chung 1 MySQL database** (không tách DB riêng từng service) và giao tiếp HTTP nội bộ. Đây là "Microservices Lite" phù hợp với team nhỏ và scope V1.

### 1.2. Service Breakdown

| Service | Port | Trách nhiệm |
|---------|------|-------------|
| `api-gateway` | 8000 | Reverse proxy, auth middleware, route điều phối |
| `auth-service` | 8001 | Login, logout, JWT issue/refresh |
| `conversation-service` | 8002 | Conversations, messages, inbox |
| `customer-service` | 8003 | Customers, notes |
| `product-service` | 8004 | Products, variants, inventory |
| `order-service` | 8005 | Orders, order items, status transitions |
| `ai-service` | 8006 | AI processing, FAQ config, payment template |
| `webhook-service` | 8007 | Facebook/Zalo webhook handlers |
| `dashboard-service` | 8008 | Stats aggregation |
| `realtime-service` | 8009 | Socket.IO server |
| `platform-service` | 8010 | Platform connections, token management |

### 1.3. Sơ đồ kiến trúc

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                            │
│                    React 18 SPA (Vite + MUI)                        │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS + WSS
┌───────────────────────────▼─────────────────────────────────────────┐
│                       API GATEWAY (:8000)                           │
│         FastAPI — JWT verification, rate limiting, routing          │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬─────────┘
   │      │      │      │      │      │      │      │      │
:8001  :8002  :8003  :8004  :8005  :8006  :8007  :8008  :8009 :8010
Auth  Conv  Cust  Prod  Order   AI   Hook  Dash  RT   Platform
                                                     (Socket.IO)

         ┌──────────────────────────────────────────────┐
         │           Shared Infrastructure               │
         │  MySQL 8.0 │ Redis 7 │ Celery Workers        │
         │  (shared DB, schema-per-service namespacing)  │
         └──────────────────────────────────────────────┘

         ┌──────────────────────────────────────────────┐
         │           External APIs                       │
         │  Facebook Graph API │ Zalo OA API            │
         │  Google Gemini 1.5 Pro API                   │
         └──────────────────────────────────────────────┘
```

### 1.4. Data Flow — Tin nhắn đến

```
Facebook/Zalo → POST /webhooks/:platform (webhook-service :8007)
  → Verify signature
  → Parse message
  → HTTP POST → customer-service: upsert customer
  → HTTP POST → conversation-service: upsert conversation + save message
  → conversation-service → publish task to Redis Queue
  → realtime-service: emit 'message:new' → Browser (Socket.IO)
  → ai-service Celery worker: nhận task
    → Load context (products, FAQs, history)
    → Call Gemini 1.5 Pro API
    → Save AI reply via conversation-service
    → Send reply via platform-service
    → realtime-service: emit 'message:new' → Browser
```

---

## 2. Tech Stack — Đã phê duyệt

### 2.1. Bảng tech stack chính thức

| Layer | Lựa chọn | Phiên bản | Ghi chú |
|-------|----------|-----------|---------|
| **Kiến trúc** | Microservices (Lite) | — | Shared DB, HTTP nội bộ |
| **Backend Language** | Python | 3.12 | |
| **Backend Framework** | FastAPI | 0.115.x | Auto OpenAPI docs, async native |
| **ORM** | SQLAlchemy | 2.x | Async support, type-safe |
| **DB Migration** | Alembic | — | Pair với SQLAlchemy |
| **Data Validation** | Pydantic | 2.x | Native FastAPI integration |
| **Database** | MySQL | 8.0 | |
| **Session/Cache/Queue** | Redis | 7.x | JWT blacklist + Celery broker |
| **Task Queue** | Celery | 5.x | Python-native, mature, Redis broker |
| **Realtime** | Socket.IO (python-socketio) | 5.x | Server-side Python Socket.IO |
| **AI Provider** | Google Gemini 1.5 Pro | API | Chất lượng cao hơn Flash |
| **Frontend Framework** | React | 18.x | |
| **Frontend Build** | Vite | 5.x | |
| **Frontend UI Library** | Material UI (MUI) | v5/v6 | Google Material Design |
| **Frontend State** | Zustand | 4.x | Simple, no boilerplate |
| **Frontend Routing** | React Router | 6.x | |
| **Frontend HTTP** | Axios | 1.x | |
| **Frontend Realtime** | Socket.IO Client | 4.x | |
| **Authentication** | JWT (RS256) | — | Access token + Refresh token |
| **File Storage** | Local disk → Cloudinary | — | Phase 1 → Phase 2 |
| **Deployment** | Local + ngrok | — | Development/Demo |

### 2.2. Lý do điều chỉnh so với khuyến nghị ban đầu

| Quyết định | Khuyến nghị | Chọn | Implication |
|------------|-------------|------|-------------|
| Kiến trúc | Monolith Modular | **Microservices** | Setup phức tạp hơn, cần Docker Compose để quản lý services |
| Backend | Node.js + Express | **Python + FastAPI** | Cần Celery thay BullMQ; FastAPI auto-docs là lợi thế lớn |
| Database | PostgreSQL | **MySQL** | Một số syntax khác nhau; JSON column support tốt từ MySQL 5.7+ |
| AI | Gemini Flash | **Gemini Pro** | Chi phí cao hơn ~3x, nhưng chất lượng reasoning và tiếng Việt tốt hơn rõ ràng |
| UI Library | shadcn/ui | **MUI** | MUI có DataGrid, DatePicker, nhiều component admin-ready sẵn |
| Auth | Session-based | **JWT** | Cần cẩn thận implement refresh token + blacklist cho logout |
| Deployment | VPS + Docker | **Local + ngrok** | Chỉ dùng cho dev/demo; cần cấu hình ngrok cho Facebook/Zalo webhooks |

### 2.3. Lưu ý về JWT với Microservices

> [!IMPORTANT]
> JWT stateless là lợi thế khi có nhiều services — mỗi service tự verify token mà không cần gọi auth-service.
>
> **Tuy nhiên cần implement:**
> - `access_token`: ngắn hạn (15 phút)
> - `refresh_token`: dài hạn (7 ngày), lưu trong Redis để có thể revoke khi logout
> - **Logout flow:** Blacklist `jti` (JWT ID) của access token trong Redis cho đến hết hạn

---

## 3. Cấu trúc thư mục dự án

```
SocialCart/
├── docs/
│   └── ...
│
├── services/
│   ├── api-gateway/             # FastAPI gateway
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── middleware/
│   │   │   │   ├── auth.py      # JWT verification middleware
│   │   │   │   └── rate_limit.py
│   │   │   └── routes/          # Proxy routes to downstream services
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── auth-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models.py        # SQLAlchemy models
│   │   │   ├── schemas.py       # Pydantic schemas
│   │   │   ├── routers/
│   │   │   │   └── auth.py      # /login, /logout, /refresh, /me
│   │   │   └── services/
│   │   │       ├── jwt.py       # Token generation/verification
│   │   │       └── auth.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── conversation-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── routers/
│   │   │   │   ├── conversations.py
│   │   │   │   └── messages.py
│   │   │   └── services/
│   │   │       ├── conversation.py
│   │   │       └── queue.py     # Publish to Redis (Celery)
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── customer-service/
│   ├── product-service/
│   ├── order-service/
│   ├── ai-service/              # AI processing + Celery workers
│   │   ├── app/
│   │   │   ├── main.py          # FastAPI (FAQ/config endpoints)
│   │   │   ├── celery_app.py    # Celery app definition
│   │   │   ├── tasks/
│   │   │   │   └── process_message.py  # AI worker task
│   │   │   ├── gemini/
│   │   │   │   ├── client.py    # Gemini API wrapper
│   │   │   │   └── prompts.py   # Prompt templates
│   │   │   └── state_machine/
│   │   │       └── conversation.py     # AI flow state machine
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── webhook-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   ├── facebook.py
│   │   │   │   └── zalo.py
│   │   │   └── services/
│   │   │       ├── signature.py # Webhook signature verification
│   │   │       └── dispatcher.py
│   │   └── Dockerfile
│   │
│   ├── platform-service/        # Platform connections + token management
│   ├── dashboard-service/
│   └── realtime-service/        # python-socketio server
│       ├── app/
│       │   ├── main.py
│       │   └── events.py        # Socket.IO event handlers
│       └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── shared/
│   │   ├── pages/
│   │   │   ├── Login/
│   │   │   ├── Dashboard/
│   │   │   ├── Inbox/
│   │   │   ├── Customers/
│   │   │   ├── Products/
│   │   │   ├── Orders/
│   │   │   └── Settings/
│   │   ├── stores/              # Zustand stores
│   │   ├── services/            # Axios API calls
│   │   ├── socket/              # Socket.IO client
│   │   ├── theme/               # MUI theme customization
│   │   ├── types/               # TypeScript types
│   │   ├── router.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
│
├── shared/
│   └── db/
│       ├── migrations/          # Alembic migrations (shared)
│       └── alembic.ini
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 4. Database Design (MySQL + SQLAlchemy)

### 4.1. Chiến lược shared database

Tất cả services dùng chung 1 MySQL database. Mỗi service sở hữu các bảng của mình. Migration quản lý tập trung qua Alembic trong `shared/db/`.

### 4.2. SQLAlchemy Models

```python
# shared/db/models.py — tất cả models trong 1 file (reference)
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, Enum, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

# ===== ENUMS =====
class Platform(str, enum.Enum):
    FACEBOOK = "FACEBOOK"
    ZALO = "ZALO"

class ConnectionStatus(str, enum.Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"

class ConversationStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"

class AiStatus(str, enum.Enum):
    AI_HANDLING = "AI_HANDLING"
    NEEDS_SELLER = "NEEDS_SELLER"
    SELLER_HANDLING = "SELLER_HANDLING"

class MessageSender(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    SELLER = "SELLER"
    AI = "AI"

class MessageStatus(str, enum.Enum):
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"

class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPING = "SHIPPING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

# ===== AUTH =====
class User(Base):
    __tablename__ = "users"
    id            = Column(String(36), primary_key=True)
    email         = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=func.now())
    updated_at    = Column(DateTime, default=func.now(), onupdate=func.now())

# ===== PLATFORM CONNECTIONS =====
class PlatformConnection(Base):
    __tablename__ = "platform_connections"
    id            = Column(String(36), primary_key=True)
    platform      = Column(Enum(Platform), nullable=False, unique=True)
    account_id    = Column(String(255))           # FB Page ID / Zalo OA ID
    account_name  = Column(String(255))
    account_type  = Column(String(50))            # "OA" | "personal"
    access_token  = Column(Text)                  # Encrypted
    refresh_token = Column(Text)                  # Encrypted (Zalo)
    token_expires_at = Column(DateTime)
    status        = Column(Enum(ConnectionStatus), default=ConnectionStatus.DISCONNECTED)
    error_message = Column(Text)
    connected_at  = Column(DateTime)
    created_at    = Column(DateTime, default=func.now())
    updated_at    = Column(DateTime, default=func.now(), onupdate=func.now())

# ===== CUSTOMERS =====
class Customer(Base):
    __tablename__ = "customers"
    id               = Column(String(36), primary_key=True)
    platform         = Column(Enum(Platform), nullable=False)
    platform_user_id = Column(String(255), nullable=False)
    display_name     = Column(String(255))
    avatar_url       = Column(String(500))
    created_at       = Column(DateTime, default=func.now())
    updated_at       = Column(DateTime, default=func.now(), onupdate=func.now())
    notes            = relationship("CustomerNote", back_populates="customer")
    conversations    = relationship("Conversation", back_populates="customer")
    orders           = relationship("Order", back_populates="customer")

    __table_args__ = (
        UniqueConstraint("platform", "platform_user_id"),
    )

class CustomerNote(Base):
    __tablename__ = "customer_notes"
    id          = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    content     = Column(Text, nullable=False)
    created_at  = Column(DateTime, default=func.now())
    customer    = relationship("Customer", back_populates="notes")

# ===== CONVERSATIONS & MESSAGES =====
class Conversation(Base):
    __tablename__ = "conversations"
    id               = Column(String(36), primary_key=True)
    platform         = Column(Enum(Platform), nullable=False)
    platform_chat_id = Column(String(255), nullable=False)
    customer_id      = Column(String(36), ForeignKey("customers.id"), nullable=False)
    status           = Column(Enum(ConversationStatus), default=ConversationStatus.NEW)
    ai_status        = Column(Enum(AiStatus), default=AiStatus.AI_HANDLING)
    is_read          = Column(Boolean, default=False)
    last_message_at  = Column(DateTime)
    ai_context       = Column(JSON)               # AI state machine context
    created_at       = Column(DateTime, default=func.now())
    updated_at       = Column(DateTime, default=func.now(), onupdate=func.now())
    customer         = relationship("Customer", back_populates="conversations")
    messages         = relationship("Message", back_populates="conversation")
    orders           = relationship("Order", back_populates="conversation")

    __table_args__ = (
        UniqueConstraint("platform", "platform_chat_id"),
        Index("idx_conversations_last_message_at", "last_message_at"),
        Index("idx_conversations_status", "status"),
        Index("idx_conversations_ai_status", "ai_status"),
    )

class Message(Base):
    __tablename__ = "messages"
    id              = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    sender          = Column(Enum(MessageSender), nullable=False)
    content         = Column(Text, nullable=False)
    status          = Column(Enum(MessageStatus), default=MessageStatus.SENT)
    platform_msg_id = Column(String(255))         # ID từ platform (để dedup)
    created_at      = Column(DateTime, default=func.now())
    conversation    = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("idx_messages_conversation_created", "conversation_id", "created_at"),
    )

# ===== PRODUCTS =====
class Product(Base):
    __tablename__ = "products"
    id          = Column(String(36), primary_key=True)
    name        = Column(String(200), nullable=False)
    description = Column(Text)
    image_url   = Column(String(500))
    status      = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE)
    created_at  = Column(DateTime, default=func.now())
    updated_at  = Column(DateTime, default=func.now(), onupdate=func.now())
    variants    = relationship("Variant", back_populates="product", cascade="all, delete")

class Variant(Base):
    __tablename__ = "variants"
    id                  = Column(String(36), primary_key=True)
    product_id          = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"))
    name                = Column(String(100), nullable=False)
    price               = Column(Integer, nullable=False)   # VNĐ — số nguyên
    stock               = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=0)
    created_at          = Column(DateTime, default=func.now())
    updated_at          = Column(DateTime, default=func.now(), onupdate=func.now())
    product             = relationship("Product", back_populates="variants")
    order_items         = relationship("OrderItem", back_populates="variant")

# ===== ORDERS =====
class Order(Base):
    __tablename__ = "orders"
    id              = Column(String(36), primary_key=True)
    order_code      = Column(String(36), unique=True, nullable=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id"))
    customer_id     = Column(String(36), ForeignKey("customers.id"), nullable=False)
    status          = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    customer_name   = Column(String(100), nullable=False)
    phone_number    = Column(String(20), nullable=False)
    address         = Column(String(500), nullable=False)
    note            = Column(Text)
    total_amount    = Column(Integer, nullable=False)       # VNĐ — số nguyên
    created_at      = Column(DateTime, default=func.now())
    updated_at      = Column(DateTime, default=func.now(), onupdate=func.now())
    customer        = relationship("Customer", back_populates="orders")
    conversation    = relationship("Conversation", back_populates="orders")
    items           = relationship("OrderItem", back_populates="order")

    __table_args__ = (
        Index("idx_orders_status", "status"),
        Index("idx_orders_customer_id", "customer_id"),
    )

class OrderItem(Base):
    __tablename__ = "order_items"
    id           = Column(String(36), primary_key=True)
    order_id     = Column(String(36), ForeignKey("orders.id"), nullable=False)
    variant_id   = Column(String(36), ForeignKey("variants.id"), nullable=False)
    # Snapshot tại thời điểm đặt
    product_name = Column(String(200), nullable=False)
    variant_name = Column(String(100), nullable=False)
    unit_price   = Column(Integer, nullable=False)
    quantity     = Column(Integer, nullable=False)
    subtotal     = Column(Integer, nullable=False)         # unit_price * quantity
    order        = relationship("Order", back_populates="items")
    variant      = relationship("Variant", back_populates="order_items")

# ===== AI CONFIG =====
class AiFaq(Base):
    __tablename__ = "ai_faqs"
    id         = Column(String(36), primary_key=True)
    question   = Column(String(500), nullable=False)
    answer     = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AiConfig(Base):
    __tablename__ = "ai_config"
    id                    = Column(String(36), primary_key=True)
    bank_account_number   = Column(String(20))
    bank_name             = Column(String(100))
    bank_account_holder   = Column(String(100))
    order_timeout_seconds = Column(Integer, default=86400)  # 24 giờ
    updated_at            = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 4.3. Quy tắc tiền tệ

> [!IMPORTANT]
> Tất cả giá trị tiền lưu dưới dạng **số nguyên VNĐ** (INT). Ví dụ: 150.000đ → `150000`. Không dùng DECIMAL hoặc FLOAT.

---

## 5. Backend Design (FastAPI — Services)

### 5.1. API Endpoint Catalog

**API Gateway** forward tất cả requests. Base URL của client: `http://localhost:8000/api/v1`

```
# Auth (→ auth-service)
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me

# Conversations (→ conversation-service)
GET    /api/v1/conversations
GET    /api/v1/conversations/{id}
GET    /api/v1/conversations/{id}/messages
POST   /api/v1/conversations/{id}/messages        # Người bán gửi
PATCH  /api/v1/conversations/{id}/ai-status       # Bật/tắt AI
PATCH  /api/v1/conversations/{id}/status

# Customers (→ customer-service)
GET    /api/v1/customers
GET    /api/v1/customers/{id}
POST   /api/v1/customers/{id}/notes
DELETE /api/v1/customers/{id}/notes/{note_id}

# Products (→ product-service)
GET    /api/v1/products
POST   /api/v1/products
GET    /api/v1/products/{id}
PUT    /api/v1/products/{id}
DELETE /api/v1/products/{id}
POST   /api/v1/products/{id}/variants
PUT    /api/v1/products/{id}/variants/{variant_id}
DELETE /api/v1/products/{id}/variants/{variant_id}

# Orders (→ order-service)
GET    /api/v1/orders
POST   /api/v1/orders                             # Tạo thủ công
GET    /api/v1/orders/{id}
PATCH  /api/v1/orders/{id}/status

# Dashboard (→ dashboard-service)
GET    /api/v1/dashboard/stats

# Platform connections (→ platform-service)
GET    /api/v1/connections
POST   /api/v1/connections/facebook/oauth/start
GET    /api/v1/connections/facebook/oauth/callback
DELETE /api/v1/connections/facebook
POST   /api/v1/connections/zalo/oauth/start
GET    /api/v1/connections/zalo/oauth/callback
DELETE /api/v1/connections/zalo

# AI Config (→ ai-service)
GET    /api/v1/ai-config
PUT    /api/v1/ai-config
GET    /api/v1/ai-config/faqs
POST   /api/v1/ai-config/faqs
PUT    /api/v1/ai-config/faqs/{id}
DELETE /api/v1/ai-config/faqs/{id}

# Webhooks (→ webhook-service, bypass gateway auth)
POST   /webhooks/facebook
GET    /webhooks/facebook
POST   /webhooks/zalo

# Health
GET    /health
```

### 5.2. Response Format chuẩn (Pydantic)

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T

class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    meta: dict  # { "total": int, "page": int, "limit": int }

class ErrorResponse(BaseModel):
    success: bool = False
    error: dict   # { "code": str, "message": str, "details": Optional[list] }
```

### 5.3. FastAPI Service Template

```python
# Mỗi service có cấu trúc tương tự:
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Conversation Service", version="1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"])  # Gateway handles auth

# Lifespan: tạo DB pool khi start, đóng khi stop
@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health")
async def health(): return {"status": "ok"}

# Routers
app.include_router(conversations_router, prefix="/conversations")
app.include_router(messages_router, prefix="/conversations/{conv_id}/messages")
```

---

## 6. Frontend Design (React + MUI)

### 6.1. MUI Theme

```typescript
// src/theme/index.ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary:   { main: '#1976d2' },
    secondary: { main: '#dc004e' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif',
  },
  components: {
    MuiButton: {
      defaultProps: { disableElevation: true }
    }
  }
});
```

### 6.2. Route Structure

```typescript
/login              → <LoginPage>
/                   → redirect → /dashboard
/dashboard          → <DashboardPage>
/inbox              → <InboxPage> (conversation list)
/inbox/:id          → <InboxPage> (với conversation panel mở)
/customers          → <CustomersPage>
/customers/:id      → <CustomerDetailPage>
/products           → <ProductsPage>
/products/new       → <ProductFormPage>
/products/:id/edit  → <ProductFormPage>
/orders             → <OrdersPage>
/orders/:id         → <OrderDetailPage>
/settings           → redirect → /settings/connections
/settings/connections → <ConnectionsPage>
/settings/ai          → <AiConfigPage>
```

### 6.3. Zustand Store Design

```typescript
// auth.store.ts
interface AuthStore {
  user: User | null;
  accessToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  checkSession: () => Promise<void>;
}

// inbox.store.ts
interface InboxStore {
  conversations: Conversation[];
  selectedId: string | null;
  messages: Record<string, Message[]>;
  filters: { platform?: Platform; status?: ConversationStatus };
  unreadCount: number;
  fetchConversations: () => Promise<void>;
  selectConversation: (id: string) => void;
  sendMessage: (conversationId: string, content: string) => Promise<void>;
  toggleAI: (conversationId: string) => Promise<void>;
  addIncomingMessage: (message: Message) => void;
}
```

### 6.4. Axios — JWT Interceptors

```typescript
// services/api.ts
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL });

// Gắn access token vào mọi request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto refresh khi gặp 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      await useAuthStore.getState().refreshToken();
      return api.request(error.config);  // Retry request
    }
    return Promise.reject(error);
  }
);
```

---

## 7. AI Chatbot Design (Gemini 1.5 Pro)

### 7.1. Celery Task — AI Worker

```python
# ai-service/app/tasks/process_message.py
from celery import shared_task
import httpx
from ..gemini.client import call_gemini
from ..state_machine.conversation import AiStateMachine

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    soft_time_limit=28,   # Celery soft limit (28s → raise exception)
    time_limit=30         # Hard kill (30s)
)
def process_incoming_message(self, conversation_id: str, message_content: str):
    try:
        # 1. Load conversation context
        conv = get_conversation_with_context(conversation_id)

        # 2. Guards
        if conv.ai_status == AiStatus.SELLER_HANDLING:
            return
        if is_timed_out(conv.ai_context):
            handle_timeout(conversation_id)
            return

        # 3. Build context cho Gemini
        context = build_ai_context(conv)

        # 4. Call Gemini 1.5 Pro
        ai_response = call_gemini(context, message_content)

        # 5. Handle action
        handler = AiStateMachine(conversation_id)
        handler.handle(ai_response)

        # 6. Emit Socket.IO event
        emit_to_seller("message:new", {"conversation_id": conversation_id})

    except SoftTimeLimitExceeded:
        # AI timeout → escalate
        escalate_to_seller(conversation_id)
    except Exception as exc:
        self.retry(exc=exc)
```

### 7.2. AI Context State Machine

```python
# ai-service/app/state_machine/conversation.py
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

class AiState(str, Enum):
    IDLE = "IDLE"
    COLLECTING_ORDER_INFO = "COLLECTING_ORDER_INFO"
    WAITING_CONFIRM = "WAITING_CONFIRM"
    ORDER_CREATED = "ORDER_CREATED"
    ESCALATED = "ESCALATED"

class OrderStep(str, Enum):
    PRODUCT = "PRODUCT"
    VARIANT = "VARIANT"
    QUANTITY = "QUANTITY"
    MORE_ITEMS = "MORE_ITEMS"
    NAME = "NAME"
    PHONE = "PHONE"
    ADDRESS = "ADDRESS"
    CONFIRM = "CONFIRM"

@dataclass
class OrderDraftItem:
    product_id: str
    product_name: str
    variant_id: str
    variant_name: str
    quantity: int
    unit_price: int

@dataclass
class AiContext:
    state: AiState = AiState.IDLE
    order_draft: Optional[dict] = None
    last_activity_at: str = ""
    failed_intent_count: int = 0
```

### 7.3. Gemini Prompt Design

```python
# ai-service/app/gemini/prompts.py

SYSTEM_PROMPT = """
Bạn là trợ lý bán hàng AI của shop. Nhiệm vụ:
1. Trả lời câu hỏi dựa trên thông tin sản phẩm và FAQ được cung cấp.
2. Hỗ trợ khách đặt hàng theo quy trình.
3. CHỈ sử dụng thông tin được cung cấp. KHÔNG bịa thêm.
4. Trả lời bằng tiếng Việt, thân thiện và ngắn gọn.

LUÔN trả về JSON theo format:
{
  "action": "REPLY" | "COLLECT_INFO" | "CREATE_ORDER" | "UPDATE_ORDER" | "ESCALATE",
  "message": "Nội dung gửi cho khách (nếu có)",
  "order_data": {...},     // Chỉ khi action = CREATE_ORDER
  "update_data": {...},    // Chỉ khi action = UPDATE_ORDER
  "next_step": "..."       // Bước tiếp theo trong flow đặt hàng
}

Thông tin sản phẩm (chỉ ACTIVE):
{product_catalog}

FAQ:
{faq_list}

Trạng thái AI hiện tại: {ai_state}
Draft đơn hàng (nếu có): {order_draft}
"""

def build_user_context(conversation_history: list, new_message: str) -> list:
    """Build message list cho Gemini multi-turn conversation."""
    messages = []
    for msg in conversation_history[-20:]:  # 20 tin nhắn gần nhất
        role = "user" if msg.sender == "CUSTOMER" else "model"
        messages.append({"role": role, "parts": [{"text": msg.content}]})
    messages.append({"role": "user", "parts": [{"text": new_message}]})
    return messages
```

### 7.4. Timeout via Celery ETA

```python
# Khi AI bắt đầu COLLECTING_ORDER_INFO
check_conversation_timeout.apply_async(
    args=[conversation_id],
    countdown=ai_config.order_timeout_seconds,
    task_id=f"timeout-{conversation_id}"
)

# Khi có tin nhắn mới → revoke job cũ, tạo lại
celery_app.control.revoke(f"timeout-{conversation_id}", terminate=False)
# ... tạo lại như trên
```

---

## 8. Tích hợp nền tảng

### 8.1. Facebook Messenger

- **Webhook:** `POST /webhooks/facebook` (webhook-service, bypass auth)
- **Verification:** `GET /webhooks/facebook?hub.verify_token=...`
- **Signature:** Verify `X-Hub-Signature-256` header với HMAC-SHA256

```python
# webhook-service/app/services/signature.py
import hmac, hashlib

def verify_facebook_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    expected = "sha256=" + hmac.new(
        app_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

> [!WARNING]
> Facebook App cần được review cho `pages_messaging` permission trước khi nhận tin từ người dùng thực. Trong dev, test với Facebook test accounts.

### 8.2. Zalo OA (V1 — OA Only)

- **API:** Zalo OA Open API v3
- **Token:** Access token hết hạn sau 1 giờ → auto refresh với refresh token (90 ngày)
- **Token refresh:** Celery periodic task mỗi 50 phút (platform-service)

```python
# platform-service — Celery beat schedule
CELERYBEAT_SCHEDULE = {
    "refresh-zalo-token": {
        "task": "tasks.refresh_zalo_token",
        "schedule": crontab(minute="*/50"),  # Mỗi 50 phút
    }
}
```

> [!CAUTION]
> **Zalo cá nhân:** V1 chỉ hỗ trợ Zalo OA (đã được người dùng xác nhận). DB có trường `account_type` sẵn sàng cho V2.

### 8.3. Token Encryption (AES-256-GCM)

```python
# shared/utils/crypto.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, base64

def encrypt_token(plaintext: str, key: bytes) -> str:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()

def decrypt_token(ciphertext: str, key: bytes) -> str:
    data = base64.b64decode(ciphertext)
    nonce, ct = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode()
```

---

## 9. Realtime & Job Queue

### 9.1. Celery Configuration

```python
# ai-service/app/celery_app.py
from celery import Celery

celery_app = Celery(
    "socialcart",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_concurrency=4,          # 4 concurrent AI jobs
    task_soft_time_limit=28,
    task_time_limit=30,
)
```

### 9.2. Socket.IO — python-socketio

```python
# realtime-service/app/main.py
import socketio
from fastapi import FastAPI

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=FRONTEND_URL
)

app = FastAPI()
socket_app = socketio.ASGIApp(sio, app)

@sio.event
async def connect(sid, environ, auth):
    # Verify JWT token từ auth dict
    if not verify_jwt(auth.get("token")):
        raise ConnectionRefusedError("Unauthorized")
    await sio.enter_room(sid, "seller-room")

@sio.event
async def inbox_join(sid, data):
    await sio.enter_room(sid, f"conversation:{data['conversation_id']}")

# Helper để emit từ các service khác (via Redis pub/sub)
async def emit_to_seller(event: str, data: dict):
    await sio.emit(event, data, room="seller-room")
```

### 9.3. Cross-Service Events (Redis Pub/Sub)

Các services publish events → realtime-service subscribe và forward tới browser:

```python
# realtime-service/app/events.py
import redis.asyncio as aioredis

CHANNELS = ["message:new", "conversation:updated", "order:created", "dashboard:stats:updated"]

async def subscribe_and_forward():
    r = aioredis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe(*CHANNELS)
    async for message in pubsub.listen():
        if message["type"] == "message":
            event = message["channel"]
            data = json.loads(message["data"])
            await sio.emit(event, data, room="seller-room")
```

---

## 10. Authentication (JWT)

### 10.1. JWT Flow

```
Login → auth-service tạo:
  access_token:  JWT, expires 15 phút, signed RS256
  refresh_token: Opaque token (UUID), expires 7 ngày, lưu Redis

Request → API Gateway verify access_token
  → Valid: forward to downstream service
  → Expired (401): Client dùng refresh_token để lấy access_token mới

Logout → auth-service:
  → Xóa refresh_token khỏi Redis
  → Blacklist access_token jti trong Redis (TTL = remaining expiry)
```

### 10.2. JWT Claims

```python
# Payload của access_token
{
  "sub": "user_id",
  "email": "seller@example.com",
  "jti": "unique-jwt-id",    # Để blacklist khi logout
  "iat": 1700000000,
  "exp": 1700000900           # 15 phút
}
```

### 10.3. API Gateway Auth Middleware

```python
# api-gateway/app/middleware/auth.py
from fastapi import Request, HTTPException
import jwt, redis

async def verify_token(request: Request):
    # Skip auth cho webhook và login
    if request.url.path.startswith("/webhooks"):
        return
    if request.url.path == "/api/v1/auth/login":
        return

    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(401, "Missing token")

    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

    # Kiểm tra blacklist
    if await redis_client.get(f"blacklist:{payload['jti']}"):
        raise HTTPException(401, "Token revoked")

    request.state.user_id = payload["sub"]
```

---

## 11. File Storage

### 11.1. Phase 1: Local Disk

```python
# product-service — upload endpoint
from fastapi import UploadFile
import aiofiles, uuid

@router.post("/{product_id}/image")
async def upload_image(product_id: str, file: UploadFile):
    # Validate
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(422, "Chỉ hỗ trợ JPG và PNG")
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(422, "File tối đa 5MB")

    # Save
    filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    path = f"uploads/products/{filename}"
    async with aiofiles.open(path, "wb") as f:
        await f.write(await file.read())

    image_url = f"{BASE_URL}/uploads/products/{filename}"
    # Update product.image_url in DB
    ...
    return {"image_url": image_url}
```

### 11.2. Phase 2: Cloudinary (migration path)

Chỉ thay đổi logic upload, không thay đổi schema DB — `image_url` vẫn là cột String(500).

---

## 12. Environment & Configuration

### 12.1. .env.example (root)

```bash
# Common
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=socialcart
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=socialcart_db
DATABASE_URL=mysql+aiomysql://socialcart:your_password@localhost:3306/socialcart_db

REDIS_URL=redis://localhost:6379

# JWT
JWT_PRIVATE_KEY_PATH=./keys/private.pem
JWT_PUBLIC_KEY_PATH=./keys/public.pem

# Encryption
ENCRYPTION_KEY=<32-byte-hex>

# Facebook
FB_APP_ID=
FB_APP_SECRET=
FB_WEBHOOK_VERIFY_TOKEN=<random-string>

# Zalo
ZALO_APP_ID=
ZALO_APP_SECRET=
ZALO_WEBHOOK_SECRET=

# Google Gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-pro

# Services (internal URLs)
AUTH_SERVICE_URL=http://localhost:8001
CONVERSATION_SERVICE_URL=http://localhost:8002
CUSTOMER_SERVICE_URL=http://localhost:8003
PRODUCT_SERVICE_URL=http://localhost:8004
ORDER_SERVICE_URL=http://localhost:8005
AI_SERVICE_URL=http://localhost:8006
WEBHOOK_SERVICE_URL=http://localhost:8007
DASHBOARD_SERVICE_URL=http://localhost:8008
REALTIME_SERVICE_URL=http://localhost:8009
PLATFORM_SERVICE_URL=http://localhost:8010

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
VITE_SOCKET_URL=http://localhost:8009

# ngrok (development)
NGROK_AUTHTOKEN=
NGROK_DOMAIN=your-domain.ngrok-free.app
```

### 12.2. Pydantic Settings (Fail-fast)

```python
# shared/config.py — dùng trong mọi service
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    gemini_api_key: str
    encryption_key: str

    class Config:
        env_file = ".env"

settings = Settings()  # Raise ValidationError nếu thiếu biến → fail fast
```

---

## 13. Deployment (Local + ngrok)

### 13.1. Local Development Setup

```
Máy local
├── Docker Compose
│   ├── mysql:8.0        (:3306)
│   └── redis:7          (:6379)
│
├── Python services (chạy riêng với uvicorn)
│   ├── api-gateway      (:8000)
│   ├── auth-service     (:8001)
│   ├── conversation-service (:8002)
│   ├── ... (các services khác)
│   ├── ai-service       (:8006) + celery worker
│   ├── webhook-service  (:8007)
│   └── realtime-service (:8009)
│
├── React frontend (Vite dev server)   (:5173)
│
└── ngrok → expose webhook-service ra internet
    ngrok http 8007 --domain=your-domain.ngrok-free.app
```

### 13.2. docker-compose.yml (Infrastructure only)

```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: socialcart_db
      MYSQL_USER: socialcart
      MYSQL_PASSWORD: your_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

### 13.3. Scripts để khởi động

```bash
# 1. Start infrastructure
docker-compose up -d mysql redis

# 2. Run migrations
cd shared && alembic upgrade head

# 3. Start tất cả Python services (dùng tmux hoặc multiple terminals)
./scripts/start-services.sh

# 4. Start Celery workers
celery -A services.ai_service.app.celery_app worker --loglevel=info

# 5. Start frontend
cd frontend && npm run dev

# 6. Start ngrok (cho webhooks)
ngrok http 8007 --domain=your-domain.ngrok-free.app
```

### 13.4. Cấu hình ngrok cho Webhooks

```bash
# Sau khi có ngrok URL, cấu hình trong Facebook Developer Console:
# Webhook URL: https://your-domain.ngrok-free.app/webhooks/facebook
# Verify Token: (giá trị FB_WEBHOOK_VERIFY_TOKEN trong .env)

# Zalo OA Admin:
# Webhook URL: https://your-domain.ngrok-free.app/webhooks/zalo
```

> [!IMPORTANT]
> ngrok free tier URL thay đổi mỗi lần restart (trừ khi dùng static domain với ngrok free plan). Cần cập nhật lại webhook URL trong Facebook/Zalo Developer Console mỗi lần.

---

## 14. Rủi ro kỹ thuật & Mitigation

| # | Rủi ro | Mức độ | Mitigation |
|---|--------|--------|-----------|
| 1 | **Microservices overhead lớn cho team nhỏ** | 🔴 Cao | "Microservices Lite" — shared DB, internal HTTP. Startup script tự động. |
| 2 | **Service-to-service latency** | 🟡 Trung | Internal HTTP (loopback), không đi qua network. Latency <1ms. |
| 3 | **ngrok URL thay đổi → webhook fail** | 🟡 Trung | Dùng ngrok static domain (free: 1 static domain). Hoặc script tự update webhook URL. |
| 4 | **Zalo cá nhân không có official API** | ✅ Đã quyết định | V1 chỉ Zalo OA. Schema sẵn sàng cho V2. |
| 5 | **Gemini Pro chi phí cao hơn Flash** | 🟡 Trung | Monitor usage. Có thể downgrade Flash nếu chi phí vượt ngưỡng. |
| 6 | **JWT không revoke được ngay (stateless)** | 🟡 Trung | Blacklist jti trong Redis cho logout. Refresh token trong Redis (revocable). |
| 7 | **Celery job mất khi Redis restart** | 🟠 Thấp | Redis AOF persistence. Celery retry on restart. |
| 8 | **Facebook App Review chậm** | 🟡 Trung | Test với Facebook test accounts. Submit App Review sớm. |
| 9 | **AI hallucinate thông tin** | 🟡 Trung | Structured output + grounding. Người bán luôn confirm đơn hàng. |
| 10 | **AI timeout > 30s** | 🟡 Trung | Celery soft_time_limit=28s → auto escalate "Cần người bán". |

---

## Technical Decisions Log

| ID | Quyết định | Người chọn | Ghi chú |
|----|-----------|-----------|---------|
| TD-01 | **Kiến trúc:** Microservices (Lite) | Người dùng | Shared DB, HTTP nội bộ để giảm overhead |
| TD-02 | **Backend:** Python + FastAPI + SQLAlchemy | Người dùng | Auto OpenAPI docs, tốt cho AI integration |
| TD-03 | **Database:** MySQL 8.0 | Người dùng | |
| TD-04 | **AI:** Google Gemini 1.5 Pro | Người dùng | Chất lượng > chi phí |
| TD-05 | **Queue:** Celery + Redis | — | Python-native alternative cho BullMQ |
| TD-06 | **Realtime:** Socket.IO (python-socketio) | — | Match với frontend Socket.IO client |
| TD-07 | **Frontend:** React 18 + Vite | Người dùng | |
| TD-08 | **UI Library:** Material UI (MUI) | Người dùng | Admin-ready components |
| TD-09 | **Auth:** JWT (RS256) | Người dùng | Stateless, phù hợp Microservices |
| TD-10 | **File storage:** Local → Cloudinary | Người dùng | MVP first |
| TD-11 | **Deployment:** Local + ngrok | Người dùng | Development/Demo |
| TD-12 | **Zalo V1:** OA only | Người dùng | Personal API không tồn tại chính thức |
| TD-13 | **Tiền tệ:** INT VNĐ | — | Tránh float precision errors |
| TD-14 | **Cross-service events:** Redis Pub/Sub | — | Realtime service subscribe và forward |

---

*Technical Design Document v1.1 — Approved. Tech stack đã được người dùng xác nhận.*
