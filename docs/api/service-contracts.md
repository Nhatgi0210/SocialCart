# API nội bộ, outbox và realtime

Baseline 2026-10-19; chưa có implementation. Dùng enum/ID trong [data-rules](../data-rules.md). Tài liệu này sở hữu giao tiếp không public; [OpenAPI](openapi.yaml) sở hữu HTTP client.

## 1. Ranh giới và auth

Gateway không forward `/internal/*`. Service bind loopback trong local; khi container hóa chỉ expose Gateway/realtime. Mọi call `/internal/*` cần `Authorization: Bearer <INTERNAL_SERVICE_TOKEN>` được kiểm tra constant-time, token chỉ server đọc. Không forward header internal do browser gửi. Token nội bộ là baseline demo, khi production phải đánh giá service identity/rotation riêng.

JSON success/error envelope như public API. UUID định dạng chuẩn, idempotency qua `Idempotency-Key`; mọi request có `X-Request-ID` để trace, không log raw secrets/PII. Timeout/retry có giới hạn theo deadline nghiệp vụ; request mutation retry giữ nguyên key. Worker không gọi HTTP để cập nhật kho rồi mới ghi đơn; xem transaction exception D-11.

## 2. Operation nội bộ tối thiểu

| Owner / operation | Input bắt buộc | Output và side effect |
| --- | --- | --- |
| customer `POST /internal/customers/upsert` | platform, platform_account_id, platform_user_id; name optional | Customer + created boolean; unique tuple, idempotent |
| conversation `POST /internal/incoming-messages` | platform, account_id, platform_chat_id, customer_id, platform_msg_id, text, occurred_at | Conversation + message; upsert atomically, dedupe, update unread/recency; outbox message event + AI job; trùng trả cùng IDs |
| conversation `GET /internal/conversations/{id}/ai-context` | id; history_limit mặc định/tối đa 20 | version, ai_generation, ai_status, ai_context, 20 messages; không kèm token nền tảng |
| conversation `PATCH /internal/conversations/{id}/ai-context` | expected_generation, ai_context; ai_status nếu handoff | CAS; 409 khi generation khác; tăng version và event sau commit |
| conversation `POST /internal/conversations/{id}/ai-actions` | incoming_message_id, expected_generation, action_id, reply hoặc handoff_reason | Fence worker; action_id/incoming unique, lưu reply SENDING + outbox send hoặc handoff không gửi; không nhận action confirm order |
| order `POST /internal/orders` | body như OrderCreate, actor AI, source_message_id/action_id và expected_generation | Order PENDING, created_by AI; idempotency, validate catalog; thực hiện trong serialized AI action workflow |
| order `PATCH /internal/orders/{id}` | body như OrderUpdate + actor AI + action_id và expected_generation | Chỉ PENDING; version/stock/snapshot theo data-rules; không tự confirm |
| platform `POST /internal/messages/{message_id}/dispatch` | message_id, conversation_id, content, platform, account_id, recipient_id | Kết quả accepted + provider_message_id hoặc error với certainty; timeout không rõ phải có `delivery_unknown=true`; dedupe message ID, không gửi khi đã SENT |
| product `GET /internal/catalog` | active_only=true; paging | Product + variants chưa xóa, giá/kho hiện tại; không coi cache là kiểm tra kho cuối cùng |
| ai `GET /internal/ai-config` | — | FAQs, timeout, payment template hiện hành; chỉ service được phép gọi |

Các JSON shape customer/conversation/order/message tái sử dụng component trong public OpenAPI; không định nghĩa lại kiểu ID/enum. Input webhook riêng có `account_id`, mapper sang model `platform_account_id`. Invalid returns 422, stale 409, missing 404, auth 401/403, dependency 503. Các operation trên là yêu cầu cho task owner, không phải endpoint đã hoạt động.

## 3. Độ bền và thứ tự workflow

Receipt + webhook outbox commit trước ACK. Incoming-message transaction + conversation outbox commit trước publish. Celery/dispatch có thể chạy nhiều lần; unique constraint và action key chống side effect trùng. Redis Pub/Sub có thể mất event; không dùng làm bằng chứng persist/queue durable.

AI action nhiều service cần state machine persisted theo `action_id`: validated → order_created_or_updated (nếu có) → reply_queued → done. Lặp task tiếp tục từ bước bền vững, không tạo đơn thứ hai. Người bán takeover được tuyến tính hóa với action claim tại conversation-service: claim kiểm ai_generation/ai_status trong lock; action chưa claim bị hủy, action đã commit ghi timeline rõ. Không giữ DB lock trong lúc gọi Gemini. Trước dispatch cuối kiểm quyền gửi lại; không thể hủy request provider đã nhận trước takeover, cần test và hiển thị sự kiện theo thời gian thực.

Outbox publisher đánh dấu sent sau broker acceptance; crash sau publish có thể gây redelivery, consumer phải dedupe. AI deadline từ webhook `received_at`, không reset sau mỗi retry. Retry kỹ thuật hết deadline chuyển NEEDS_SELLER. Nếu DB down trước ACK: 503; Redis down sau receipt: outbox chờ, không mất tin đã nhận.

## 4. Socket.IO contract v1

- URL `VITE_SOCKET_URL`, handshake `auth:{token:access_token}`. Kiểm JWT + session revoked; từ chối token cũ sau logout; hết token thì disconnect, client refresh qua HTTP rồi reconnect.
- Chỉ một người bán: server tự join room seller từ JWT. Client event `conversation:join` nhận `{conversation_id}`; kiểm UUID/resource tồn tại, không cho tự chọn seller room.
- Client không gửi nghiệp vụ qua socket; gửi tin/toggle/order vẫn dùng HTTP có auth/idempotency/version.

Envelope chung:

```json
{
  "schema_version": 1,
  "event_id": "9f4bd21c-f5d4-46a2-bfb0-9d1527a56011",
  "occurred_at": "2026-10-19T07:00:00Z",
  "event_type": "message:new",
  "data": {
    "conversation_id": "550e8400-e29b-41d4-a716-446655440002",
    "message_id": "550e8400-e29b-41d4-a716-446655440003"
  }
}
```

| Event | data bắt buộc | Consumer |
| --- | --- | --- |
| `message:new` | conversation_id, message_id | Refetch messages và inbox; dedupe message ID |
| `message:updated` | conversation_id, message_id, status | Delivery/retry state; refetch message |
| `conversation:updated` | conversation_id, version | Refetch status, AI, unread và recency |
| `order:created` | order_id, conversation_id, version | Refetch order list/customer panel |
| `order:updated` | order_id, conversation_id, version | Refetch detail, stock và stats |
| `dashboard:stats:updated` | changed_at | Refetch Dashboard |

`conversation_id` trong order event có thể null chỉ nếu hợp đồng tạo đơn sau này cho phép ngoài chat; hiện OrderCreate yêu cầu conversation nên luôn là UUID. Mỗi consumer bỏ event_id đã xử lý; nếu nhận version cũ không ghi đè state mới. Reconnect, focus sau offline và phát hiện gap đều refetch; không cam kết replay Pub/Sub. Không gửi access/refresh/platform token hoặc payload khách đầy đủ trong event invalidation.

## 5. Structured output của AI adapter

Baseline JSON cho output model (provider adapter phải ép schema, backend vẫn validate lại):

```json
{
  "intent": "buying_intent",
  "action": "REPLY",
  "reply": "Bạn muốn chọn size nào?",
  "needs_human": false,
  "handoff_reason": null,
  "extracted_order": {
    "items": [],
    "customer_name": null,
    "phone_number": null,
    "address": null,
    "note": null
  }
}
```

Tất cả key trên bắt buộc, không cho key lạ. `intent`: inquiry/buying_intent/ready_to_order/complaint/other; `action`: REPLY/REQUEST_CUSTOMER_CONFIRMATION/CREATE_PENDING_ORDER/UPDATE_PENDING_ORDER/HANDOFF. `reply`: string 1–10000 hoặc null khi HANDOFF; `needs_human`: boolean; `handoff_reason`: string tối đa 500 hoặc null. `items`: array `{variant_id: UUID, quantity: integer>=1}`; field chưa biết null, không dùng chuỗi rỗng thay null. Tên/phone/address theo OpenAPI; model không trả unit_price/total, sender, order status hoặc tài khoản ngân hàng mới.

HANDOFF hoặc needs_human=true thì backend không dispatch reply, chuyển NEEDS_SELLER. CREATE chỉ hợp lệ khi backend đang AWAITING_CONFIRMATION, có snapshot tóm tắt hiện hành và incoming message xác nhận từ khách; không tin riêng nhãn ready_to_order để tạo đơn. UPDATE chỉ có target order PENDING thuộc conversation; trạng thái/version kiểm lại trong transaction. Mọi action có action_id do backend tạo, source_message_id và expected_generation; model không quyết định các giá trị này.

Order-service với actor AI kiểm generation hiện hành của conversation dưới row lock trước mutation; thứ tự khóa conversation → order → variants. Không giữ lock trong lúc gọi LLM/provider. Timeline vì vậy phân biệt takeover trước/sau mutation commit; request gửi provider đã nhận trước takeover không thể thu hồi. Retry có cùng action_id tiếp tục workflow persisted thay tạo đơn mới.
