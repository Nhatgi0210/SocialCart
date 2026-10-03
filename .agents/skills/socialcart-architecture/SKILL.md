---
name: socialcart-architecture
description: >-
  Cung cap kien truc va tech stack cua du an SocialCart. Su dung khi agent can
  hieu cau truc services, ports, cong nghe su dung, hoac khi tao code moi can
  tuan thu kien truc hien co. Activate khi nguoi dung hoi ve kien truc he thong,
  cach them service moi, hoac can biet service nao chiu trach nhiem gi.
---

# SocialCart - Kien Truc He Thong

## Tech Stack (Da phe duyet)

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + Material UI (MUI) |
| Backend | FastAPI (Python 3.11) |
| Database | MySQL 8.0 + SQLAlchemy (ORM) |
| Cache/Queue | Redis 7 |
| Task Queue | Celery |
| Realtime | Socket.IO |
| AI | Google Gemini 1.5 Pro API |
| Auth | JWT (access + refresh tokens) |

## Service Map

| Service | Port | Trach nhiem chinh |
|---------|------|-------------------|
| api-gateway | 8000 | Reverse proxy, JWT middleware, routing |
| auth-service | 8001 | Login, logout, JWT issue/refresh |
| conversation-service | 8002 | Conversations, messages, unified inbox |
| customer-service | 8003 | Customers, customer notes |
| product-service | 8004 | Products, variants, inventory |
| order-service | 8005 | Orders, order items, status transitions |
| ai-service | 8006 | AI processing, FAQ config, payment templates |
| webhook-service | 8007 | Facebook/Zalo webhook handlers |
| dashboard-service | 8008 | Stats aggregation |
| realtime-service | 8009 | Socket.IO server |
| platform-service | 8010 | Platform connections, token management |

## Nguyen tac kien truc

1. Shared Database: Tat ca services dung chung 1 MySQL DB.
2. HTTP noi bo: Services giao tiep qua HTTP REST.
3. Redis Queue: AI processing va heavy tasks chay qua Celery workers.
4. API Gateway first: Moi request tu frontend deu qua api-gateway (:8000).
5. Realtime: Socket.IO server (:8009) nhan emit tu backend, push xuong browser.

## Data Flow - Tin nhan den

`
Facebook/Zalo Webhook -> webhook-service (:8007)
  -> Verify signature -> Parse message
  -> HTTP -> customer-service: upsert customer
  -> HTTP -> conversation-service: upsert conversation + save message
  -> realtime-service: emit message:new -> Browser
  -> ai-service Celery worker:
    -> Load context (products, FAQs, history)
    -> Call Gemini 1.5 Pro API
    -> Save AI reply via conversation-service
    -> Send reply via platform-service
    -> realtime-service: emit message:new -> Browser
`

## Cau truc thu muc chuan moi service

`
backend/<service-name>/
    main.py          # FastAPI app, router includes
    models.py        # SQLAlchemy models
    schemas.py       # Pydantic request/response schemas
    crud.py          # DB operations
    routes/          # API route handlers
    services/        # Business logic layer
    dependencies.py  # FastAPI Depends() functions
    requirements.txt
`
