---
name: socialcart-new-service
description: Scaffold service hoặc endpoint SocialCart theo kiến trúc, contract và migration chung đã thống nhất.
---

# SocialCart Service Implementation

Đọc [AGENTS](../../../AGENTS.md), [implementation plan](../../../docs/implementation-plan.md), [OpenAPI](../../../docs/api/openapi.yaml) và [service contracts](../../../docs/api/service-contracts.md). Chỉ tạo service/endpoint trong task; không tăng số service tự phát.

Layout backend/<service>/app/{main.py,schemas.py,dependencies.py,routers/,services/}, requirements.txt/Dockerfile khi cần. Dùng backend/shared/db cho ORM/session/migration; không copy model Integer ID hoặc tạo bảng qua create_all lúc startup. UUID, tiền nguyên, enums theo data-rules.

Lifespan mở/đóng pool; settings theo service, CORS allowlist tại biên, error envelope đúng spec. GET không làm side effect nghiệp vụ; mutation có validation/version/idempotency theo operation. Đăng ký Gateway public path, không expose internal. /health kiểm dependency bắt buộc và trả 503 nếu thiếu.

Viết migration và kiểm tra upgrade DB rỗng/seed; kiểm thử hành vi bị tác động và error/recovery phù hợp. Không giả định skeleton chạy được trước khi chạy lệnh trong setup; cập nhật contract cùng code.
