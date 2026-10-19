---
name: socialcart-ai-service
description: Implement hoặc debug FAQ, Gemini adapter, thu thập đơn và handoff SocialCart; model cần xác minh trước tích hợp live.
---

# SocialCart AI Service

Đọc [data rules §6](../../../docs/data-rules.md), [service contracts](../../../docs/api/service-contracts.md), [test plan](../../../docs/test-plan.md). ai-service :8006, Celery worker Linux/WSL2. Gemini1.5 Pro đã shutdown; chọn GEMINI_MODEL khả dụng qua EXT-01, không hardcode default cũ.

Context: catalog active + variants/stock, FAQ/policies/payment template đã cấu hình, tối đa20 message, state thu thập. Structured output gồm reply/intent/extracted fields/needs_human/reason; backend validate mọi action, giá và quyền. Không bịa thông tin hoặc thực thi action theo text tự do.

Task dùng UUID string, dedupe incoming/action ID, serialize theo conversation; snapshot ai_generation và kiểm ai_status/generation/deadline trước action/send. Unknown/error/parse/deadline30s từ nhận→NEEDS_SELLER và không gửi output lỗi. Tắt AI fence kết quả cũ. Collection timeout1–72h/mặc định24h→NEW/reset context/no order, AI sẵn sàng; không gộp hai timeout.

Flow đơn: items→variant→qty→tên→phone→địa chỉ→tóm tắt→khách xác nhận→order-service PENDING→bank template nếu có. AI không confirm; sửa chỉ PENDING; confirmed trở đi handoff. Workflow persisted action_id chống order đôi khi retry/crash; gửi qua platform-service/outbox, chỉ SENT khi provider accepted.

Không gửi reply rồi mới kiểm needs_human như mẫu cũ. Tách deterministic/simulation và live evidence; log metadata/token count nếu provider cung cấp, không log raw secret/PII.
