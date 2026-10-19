---
name: socialcart-webhook
description: Implement/debug webhook Facebook Messenger và Zalo OA, xác minh raw payload và chống xử lý trùng bền vững.
---

# SocialCart Webhooks

Đọc [OpenAPI](../../../docs/api/openapi.yaml), [data rules §5](../../../docs/data-rules.md), [service contracts](../../../docs/api/service-contracts.md). Gateway :8000 route /webhooks/facebook và /webhooks/zalo tới webhook-service :8007; raw bytes/signature header không bị đổi.

Facebook GET verify dùng FB_WEBHOOK_VERIFY_TOKEN và trả original challenge dạng text/plain, không ép int. POST verify X-Hub-Signature-256 trên raw body. Với Zalo OA, INT-01 phải xác minh signature/header/payload/token hiện hành từ official docs; không copy shape giả định trong ví dụ cũ.

Verify→durable receipt+outbox transaction→ACK. DB down trước commit trả503; signature sai403. Unique platform/account/event_id, Redis chỉ cache; không dùng SET NX trước xử lý làm nguồn exactly-once vì crash có thể mất tin. Replay/redelivery không tạo message/task/đơn mới.

Consumer upsert customer theo platform/account/user, conversation theo platform/account/chat, message theo platform/account/message ID. Publish sau commit, queue AI chỉ khi AI_HANDLING. Không gọi Gemini inline hoặc gửi token qua event. Bằng chứng local/simulated/live riêng; replay tài khoản test, không gửi khách thật khi không có chỉ thị.
