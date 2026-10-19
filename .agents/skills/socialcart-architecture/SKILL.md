---
name: socialcart-architecture
description: Kiến trúc và ranh giới service SocialCart; dùng khi cần hiểu stack, luồng dữ liệu hoặc cấu trúc code.
---

# SocialCart Architecture

Đọc [AGENTS](../../../AGENTS.md), [TDD](../../../docs/technical-design.md), [decision log](../../../docs/decisions.md). Chi tiết dữ liệu/transaction ở data-rules; HTTP ở docs/api/openapi.yaml, internal/realtime ở service-contracts.

Microservices Lite, FastAPI/Python 3.11, MySQL 8.0 dùng chung, SQLAlchemy/Alembic, Redis 7/Celery, React 18 + TypeScript + MUI. Không tự đổi kiến trúc. Gateway :8000; auth :8001, conversation :8002, customer :8003, product :8004, order :8005, ai :8006, webhook :8007, dashboard :8008, realtime :8009, platform :8010.

Code ở backend/<service>/app, model/migration chung backend/shared/db. Browser HTTP qua /api/v1; Socket.IO riêng; webhook qua Gateway giữ nguyên raw body. Receipt/outbox commit trước ACK, publish sau commit; Pub/Sub chỉ invalidation, reconnect refetch.

V1 một seller/Page/OA; AI không confirm đơn. ID UUID, tiền nguyên VNĐ. PENDING không giữ kho; order-service transaction kho là ngoại lệ ownership có giới hạn. Gemini model phải được xác minh EXT-01, không dùng model 1.5 đã shutdown. Không suy skeleton/tài liệu thành implementation đã chạy.
