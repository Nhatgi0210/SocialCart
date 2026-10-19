# Technical Design Document: SocialCart

> **Phiên bản:** 1.2 — đồng bộ triển khai 2026-10-19.
> **Trạng thái:** giữ các quyết định kiến trúc đã phê duyệt ở v1.1; bổ sung baseline kỹ thuật, chưa có implementation.
> **Nguồn:** [PRD](product-requirements.md), [Feature Spec](feature-specification.md), [Product Design](product-design.md).

[Decision log](decisions.md) phân biệt quyết định đã có, quy ước bổ sung và đầu vào còn thiếu. [Data rules](data-rules.md), [OpenAPI](api/openapi.yaml), [service contracts](api/service-contracts.md) là phần chi tiết của thiết kế này, không phải ba bản schema cạnh tranh. Các snippet v1.1 đã được thay bằng hợp đồng để tránh copy code minh họa sai vào ứng dụng.

## 1. Kiến trúc Microservices Lite

Một hộ kinh doanh, một người bán; services giao tiếp HTTP nội bộ, chung MySQL 8.0, Redis 7 cho session/queue/pubsub. Không tách DB từng service ở V1. Trình duyệt dùng Gateway cho HTTP, Socket.IO riêng cho realtime. Redis Pub/Sub chỉ invalidation, không thay dữ liệu bền vững.

| Service | Port | Trách nhiệm |
| --- | --- | --- |
| api-gateway | 8000 | Routing, auth, CORS, request ID, giới hạn request |
| auth-service | 8001 | Login/refresh/logout/me, session revoke |
| conversation-service | 8002 | Inbox, messages, unread, AI context, outgoing outbox |
| customer-service | 8003 | Upsert khách theo platform/account/user, notes |
| product-service | 8004 | Catalog, variants, stock chỉnh tay, ảnh |
| order-service | 8005 | Orders/items/snapshot, lifecycle và transaction kho |
| ai-service | 8006 | FAQ/config, Gemini adapter, Celery worker |
| webhook-service | 8007 | Verify, durable receipt/outbox, normalize incoming |
| dashboard-service | 8008 | Read-only aggregation theo ngày Việt Nam |
| realtime-service | 8009 | Socket.IO auth, phân phối event invalidation |
| platform-service | 8010 | OAuth, token mã hóa/refresh, send adapters |

Luồng incoming: provider → Gateway `/webhooks/*` → verify + receipt/outbox → ACK → worker upsert customer/conversation/message → publish after commit → UI refetch → AI task nếu còn AI_HANDLING. AI validate context/action và deadline → order-service nếu có → reply SENDING → platform dispatch → SENT/FAILED → realtime.

## 2. Tech stack và version

Python 3.11, FastAPI 0.115.x, SQLAlchemy 2.x async với aiomysql, Alembic, Pydantic 2.x; Celery 5.x; python-socketio 5.x. Frontend React 18 + TypeScript + Vite + MUI 5, TanStack Query 5, Zustand, Router 6, Axios, Socket.IO client 4.x. Auth RS256; local file storage V1, Cloudinary là hướng mở rộng.

Đây là baseline major/minor từ thiết kế; BOOT-01/02 chốt patch tương thích, pin/lock và kiểm chứng theo [setup](setup.md). Không tự nâng major hoặc tuyên bố các package đã cài.

**Gemini:** lựa chọn lịch sử là Gemini 1.5 Pro. Google ghi model này đã shutdown ngày 2025-09-29 trong [changelog chính thức](https://ai.google.dev/gemini-api/docs/changelog#september-29-2025), được đọc ngày 2026-10-19. Không dùng `gemini-1.5-pro` làm default chạy được. INT-01 cần chọn model Gemini khả dụng với tài khoản, kiểm chứng structured output/độ trễ/chi phí; `GEMINI_MODEL` để trống đến khi chốt. Không tự thay nhà cung cấp hoặc ghi một model mới là đã được người dùng chọn.

## 3. Thư mục chuẩn

```text
backend/
  <service-name>/
    app/
      __init__.py
      main.py
      schemas.py
      dependencies.py
      routers/
      services/
    requirements.txt
    Dockerfile
  shared/
    __init__.py
    config.py
    db/
      models.py
      session.py
      alembic.ini
      migrations/
  tests/
  requirements-dev.txt
frontend/src/
  components/
  pages/
  services/
  stores/
  hooks/
  socket/
  theme/
  types/
  router.tsx
  main.tsx
scripts/
docs/api/
```

Hiện các thư mục application trên là mục tiêu scaffold, chưa tồn tại. `backend/shared` là Python package chung; PYTHONPATH root backend theo setup. Service giữ business logic trong app/services và không định nghĩa model ORM trùng shared/db. Một migration tree, một lệnh upgrade trước khi start các service.

## 4. Database design

Schema nền: users; platform_connections; customers/customer_notes; conversations/messages; products/variants; orders/order_items; ai_faqs/ai_config. Bổ sung receipt/outbox, inventory_movements và request_idempotency để bảo đảm recovery. Ownership, field bổ sung, FK, unique/index/check và transaction ở [data-rules §3](data-rules.md#3-sở-hữu-bảng-và-migration).

ID UUID chuỗi 36; platform IDs chuỗi opaque; price/total integer VNĐ. Không DECIMAL/FLOAT cho tiền trong V1. Timestamp UTC, UI Asia/Ho_Chi_Minh. Conversation.status, ai_status, is_read độc lập. Order.status PENDING/CONFIRMED/SHIPPING/COMPLETED/CANCELLED. Snapshot tên/giá trên order_items, không lấy tên/giá catalog hiện tại để dựng lại đơn cũ.

PENDING không giữ kho. Confirm khóa order và variants theo thứ tự ID, kiểm tra đủ stock, cập nhật cùng transaction. Cancel từ confirmed/shipping hoàn một lần. Ngoại lệ quyền ghi variants của order-service được giới hạn bởi unit of work và movement ledger; không tách trừ kho qua HTTP rồi mới lưu order.

Xóa mềm sản phẩm/biến thể đã tham chiếu, không cascade xóa lịch sử. `version` cho order/conversation/variant; expected_version bảo vệ stale write. Schema phải có ràng buộc chống duplicate message theo platform/account/message ID và idempotency action.

## 5. Backend và Gateway

[OpenAPI](api/openapi.yaml) định nghĩa toàn bộ HTTP public, request/response, required fields, enums, pagination, auth, lỗi và ví dụ. [API README](api/README.md) giải thích side effect và retry. Không duy trì catalog endpoint thủ công khác lệch spec.

Gateway: HTTP nghiệp vụ `/api/v1/*`; webhook `/webhooks/*`; health `/health`. Không expose `/internal/*`, không forward header service auth do browser cung cấp. Webhook bỏ JWT nhưng bắt buộc xác minh chữ ký. Auth login/refresh/logout và OAuth callback có chính sách riêng trong spec; refresh không bị access-token-expired middleware chặn.

HTTP business success `{success:true,data:...}`; pagination thêm `meta`; error `{success:false,error:{code,message,details}}`. Webhook ACK/verify challenge và HTTP 204/302 có định dạng riêng theo spec. Dependency lỗi không trả 200 giả; error không lộ secret. CORS allowlist cụ thể, credentials cho refresh cookie.

Service lifespan quản lý pool/session và đóng tài nguyên. Migration không chạy riêng ở mỗi startup. Settings theo service, chỉ adapter được bật mới đòi credential. Health trả 503 nếu dependency bắt buộc chưa sẵn sàng, không expose DSN.

## 6. Frontend

Theme theo Concept B: nền `#fafaf8`, AI teal `#0d9488`, handoff cam, font Outfit có fallback hệ thống. MUI theme phải giữ focus-visible, reduced-motion và tương phản đã kiểm tra; không dùng primary/secondary mặc định của ví dụ v1.1.

Routes: `/login`, `/dashboard`, `/inbox`, `/customers`, `/customers/:id`, `/products`, `/orders`, `/orders/:id`, `/settings`. Không register/reset password/staff. Login cuối cùng về Dashboard theo AC-29; prototype vào Inbox là phạm vi mô phỏng.

TanStack Query quản lý server state; Zustand UI/session memory; Axios dùng VITE_API_URL đã gồm `/api/v1`. Refresh cookie HttpOnly, access trong memory; single-flight refresh và chỉ retry một lần sau 401, không loop. Reconnect socket/focus sau offline refetch. Không coi event là nguồn dữ liệu duy nhất.

Inbox desktop: list 360px, chat linh hoạt, customer panel; mobile list→chat có back, info toggle. Quick order là modal giữa màn hình, focus trap/Escape/return focus. UI chuẩn và recovery ở design brief; trạng thái nghiệm thu ở [prototype review](prototype-review.md).

## 7. AI và Celery

Context: catalog active/variants, FAQs, policy/payment template đã cấu hình, tối đa 20 message gần nhất, state thu thập đơn. Output có schema: reply, intent, extracted fields, needs_human/reason; backend validate, không thực thi SQL hay giá trị tiền do LLM cung cấp.

Worker tuần tự từng conversation, dedupe incoming/action ID, deadline 30 giây từ nhận. Kiểm ai_status/ai_generation trước action và gửi; tắt AI fence worker cũ. Lỗi model, parse, unknown hoặc hết deadline → NEEDS_SELLER, không gửi output lỗi. Collection timeout là cơ chế khác: 1–72 giờ, mặc định 24h, reset NEW và context, không tạo đơn.

Flow đơn: thu thập nhiều items/variant/qty/thông tin giao → tóm tắt → khách xác nhận → order-service tạo PENDING → payment template nếu có → báo chờ người bán. Sửa chỉ PENDING, đơn confirmed trở đi chuyển người bán. AI không được confirm. Workflow nhiều service persisted theo action_id để crash/retry không tạo đơn hai lần; xem service-contracts.

## 8. Tích hợp nền tảng

V1 một Facebook Page và một Zalo OA. INT-01 kiểm chứng official docs, quyền, callback, raw payload, signature, token lifecycle và tài khoản test hiện hành. Ví dụ payload/TTL cũ không đủ làm contract nhà cung cấp.

Facebook verify challenge trả nguyên chuỗi text/plain, signature xác minh raw bytes. Zalo xác minh theo tài liệu/credential OA hiện hành; không tự đoán HMAC format/header. OAuth state one-time, có hạn và gắn phiên; token platform mã hóa AES-256-GCM, không trả browser. Refresh schedule dựa expiry/provider thật, không hardcode con số đã cũ.

Webhook receipt/outbox bền vững trước ACK; duplicate bảo vệ bằng unique DB, Redis chỉ cache. Outgoing giữ SENDING đến khi provider accepted, reject thành FAILED, timeout không rõ không retry mù. Không cam kết exactly-once gửi ngoài nếu provider không hỗ trợ.

## 9. Realtime và job

Socket.IO auth JWT + session revoke; room server quyết định. Event envelope schema_version/event_id/occurred_at/type/data; events và fields cụ thể ở service-contracts §4. Publish sau commit, dedupe consumer. Redis Pub/Sub không có replay; reconnect refetch API. Outbox bền vững khác Pub/Sub. Celery worker chuẩn Linux/WSL2, không giả định worker Windows native chạy giống Linux.

## 10. Auth và session

RS256, access 15 phút, refresh opaque tối đa 7 ngày; idle session 24 giờ. Claims sub/sid/jti/iat/exp/issuer/audience; Redis lưu session và hash refresh, rotation nguyên tử. Logout revoke sid, blacklist jti hiện tại và đóng socket. Auth dependency lỗi fail closed.

Refresh HttpOnly cookie sc_refresh; SameSite=Lax, Path `/api/v1/auth`, Secure trên HTTPS; dev HTTP local có flag riêng. Origin allowlist cho thao tác auth dùng cookie; không localStorage refresh/access. Một người bán khởi tạo CLI seed, password hash; không public register. Chi tiết và test ở data-rules §7/test-plan.

## 11. File storage

V1 upload JPEG/PNG/WebP tối đa 5 MiB, kiểm bytes/MIME và đường dẫn, random filename; static URL cấu hình public, DB giữ image_url. Không dùng tên file client ghép đường dẫn. Catalog authenticated; không upload secret/PII làm fixture. Cloudinary là hướng tương lai, chưa yêu cầu tài khoản hoặc triển khai trong MVP.

## 12. Environment

[.env.example](../.env.example) là mẫu biến chính thức; [setup](setup.md) mô tả cách dùng. Không nhúng mẫu secret khác vào TDD/skill. VITE_API_URL/VITE_SOCKET_URL là public; key/token không có prefix VITE. Keys/.env không commit. Validate cấu hình theo service/flag, không bắt auth-service có Gemini secret khi AI disabled.

## 13. Local/demo deployment

Mục tiêu: Compose MySQL/Redis; Python services bind loopback; React dev server; worker Linux/WSL2; ngrok :8000 chỉ cho callback. Quy trình cài, migrate, seed, start, kiểm tra ở setup; script chưa tồn tại phải được tạo ở BOOT, không ghi đã chạy. Production deployment cần task/runbook riêng, không suy từ demo local.

## 14. Rủi ro và kiểm chứng

| Rủi ro | Xử lý / bằng chứng |
| --- | --- |
| Microservices nhiều tiến trình | Startup script/log/PID theo service và mốc, BOOT/DEMO |
| DB chung ghi chéo | Ownership + ngoại lệ transaction kho; MySQL concurrency tests |
| ACK trước persist, queue crash | Receipt/outbox, crash/replay tests |
| Gemini 1.5 đã shutdown | EXT-01 model mới khả dụng trước AI live |
| Permission/token provider đổi | INT-01 docs + live smoke từng provider |
| Pub/Sub mất event | Refetch, không dùng event làm DB |
| AI bịa/thao tác sau takeover | Schema/backend validation, fencing/deadline, deterministic failure tests |
| Callback/domain thay đổi | Ghi callback thực tế, kiểm provider delivery; không hứa quota ngrok |

[Implementation plan](implementation-plan.md) chia task; [test plan](test-plan.md) truy vết AC và ca lỗi. Mọi kết quả phân biệt static/local/simulated/live.

## Technical Decisions Log (giữ nguồn v1.1)

| ID | Quyết định |
| --- | --- |
| TD-01 | Microservices Lite, shared DB, HTTP nội bộ |
| TD-02 | Python + FastAPI + SQLAlchemy |
| TD-03 | MySQL 8.0 |
| TD-04 | Lịch sử: Gemini 1.5 Pro; đã shutdown, model khả dụng cần EXT-01 |
| TD-05 | Celery + Redis |
| TD-06 | python-socketio và Socket.IO client |
| TD-07 | React 18 + Vite |
| TD-08 | Material UI |
| TD-09 | JWT RS256 |
| TD-10 | Local file storage trước; Cloudinary sau |
| TD-11 | Local + ngrok cho development/demo |
| TD-12 | Zalo V1 OA only |
| TD-13 | Tiền nguyên VNĐ |
| TD-14 | Cross-service realtime Redis Pub/Sub, có refetch |

Quy ước bổ sung, cơ sở và phụ thuộc mới ghi riêng trong decisions.md; không gán cho người dùng các lựa chọn chưa từng được xác nhận.
