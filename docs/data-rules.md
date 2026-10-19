# Quy tắc dữ liệu và giao dịch V1

Baseline kỹ thuật 2026-10-19, đọc cùng [decision log](decisions.md), [TDD](technical-design.md) và [OpenAPI](api/openapi.yaml). Đây là quy tắc cho implementation, chưa phải schema đang chạy. Mô hình ví dụ trong TDD phải được bổ sung các trường/ràng buộc dưới đây khi viết migration.

## 1. Kiểu dữ liệu và xác thực

- ID nội bộ UUID dạng chuỗi canonical 36 ký tự. ID nền tảng là chuỗi opaque; không ép integer. `order_code` duy nhất, phục vụ hiển thị, không thay PK.
- Tiền nguyên VNĐ: `1..2147483647` cho giá bán/tổng đơn; không nhận giá từ frontend/LLM làm nguồn tính tiền. Tổng = tổng `quantity * unit_price`, kiểm tra tràn trước ghi. Không tự thêm phí ship/hoàn tiền/payment status ngoài hợp đồng V1.
- Timestamp lưu UTC (MySQL `DATETIME(6)` theo quy ước UTC); serialize RFC 3339 `Z`. UI hiển thị `Asia/Ho_Chi_Minh`; “hôm nay” Dashboard tính theo múi giờ này.
- Chuỗi trim; tên 1–100 ký tự, địa chỉ 1–500; SĐT lưu chuỗi 10–11 chữ số theo Feature Spec, không làm mất số 0 đầu. Không nhận khoảng trắng-only. Nội dung tin nhắn text 1–10000 ký tự. Quantity integer 1–1000000, stock integer 0–2147483647.
- Pagination `page>=1`, `limit=1..100` mặc định 20. Tìm kiếm theo tên không phân biệt hoa thường; cùng timestamp thì ID làm khóa sắp xếp phụ.
- Soft delete sản phẩm/biến thể đã được tham chiếu; snapshot đơn vẫn nguyên vẹn. `deleted_at` loại khỏi catalog hiện tại; không cascade xóa order item. Không còn biến thể chưa xóa thì product chuyển `INACTIVE`.

## 2. Enum chuẩn

| Trường | Giá trị API/DB | Nhãn UI |
| --- | --- | --- |
| platform | `FACEBOOK`, `ZALO` | Facebook, Zalo OA |
| conversation.status | `NEW`, `IN_PROGRESS`, `RESOLVED` | Mới, Đang xử lý, Đã xử lý |
| conversation.ai_status | `AI_HANDLING`, `NEEDS_SELLER`, `SELLER_HANDLING` | AI đang xử lý, Cần người bán, Người bán đang xử lý |
| conversation.is_read | boolean | Đã đọc/chưa đọc, độc lập hai trường trên |
| message.sender | `CUSTOMER`, `SELLER`, `AI` | Khách, Người bán, AI |
| message.status | `SENDING`, `SENT`, `FAILED` | Đang gửi, Đã gửi, Gửi thất bại |
| order.status | `PENDING`, `CONFIRMED`, `SHIPPING`, `COMPLETED`, `CANCELLED` | Chờ xác nhận, Đã xác nhận, Đang giao, Hoàn thành, Đã hủy |
| product.status | `ACTIVE`, `INACTIVE` | Đang bán, Ngừng bán |
| connection.status | `CONNECTED`, `DISCONNECTED`, `ERROR` | Đã kết nối, Chưa kết nối, Lỗi kết nối |

`NEEDS_SELLER` không phải trạng thái xử lý. Đơn hoàn thành không tự động biến hội thoại thành `RESOLVED`. Khách nhắn mới làm `is_read=false`, `status=NEW` nếu trước đó `RESOLVED`; giữ nguyên trạng thái tiếp quản AI.

## 3. Sở hữu bảng và migration

| Owner | Bảng |
| --- | --- |
| auth | users, auth session metadata trong Redis |
| platform | platform_connections |
| customer | customers, customer_notes |
| conversation | conversations, messages, conversation_outbox |
| product | products, variants |
| order | orders, order_items, inventory_movements, request_idempotency |
| ai | ai_faqs, ai_config; context hội thoại cập nhật qua conversation-service |
| webhook | webhook_receipts, webhook_outbox |

Dashboard chỉ đọc. Realtime chuyển sự kiện. Tất cả model/migration tập trung `backend/shared/db/`; service thông thường ghi bảng của mình, không tạo bảng độc lập lúc startup. Migration duy nhất chạy trước service, kiểm tra upgrade trên DB rỗng và DB có seed.

**Ngoại lệ V1:** order-service được khóa/cập nhật `variants.stock` và ghi `inventory_movements` trong cùng unit of work MySQL với orders/items; product-service vẫn sở hữu catalog và điều chỉnh kho thủ công. Cả hai phải khóa cùng hàng variant, kiểm tra expected_version khi chỉnh kho thủ công và tăng variant.version mỗi khi stock đổi. Không dùng chuỗi “HTTP trừ kho → ghi đơn” thiếu tính nguyên tử.

Ràng buộc tối thiểu:

- Customer UNIQUE `(platform, platform_account_id, platform_user_id)`; conversation UNIQUE `(platform, platform_account_id, platform_chat_id)`; message UNIQUE `(platform, platform_account_id, platform_msg_id)` cho incoming có ID. Thêm account ID/platform vào model message nếu chưa có.
- FK order/customer/conversation nhất quán: conversation phải thuộc customer được chỉ định; không cho đổi customer của đơn.
- Product/variant `deleted_at`; order `created_by=AI|SELLER`, `version>=1`; conversation và variant `version>=1`; tất cả tổng/stock/quantity có check constraint và kiểm tra ứng dụng.
- `inventory_movements` UNIQUE `(order_id, movement_type)` với `DEDUCT`/`RESTORE`; ghi chi tiết từng variant qua movement items hoặc unique thêm variant ID theo schema đã chọn, vẫn bảo đảm một movement batch mỗi lần chuyển trạng thái.
- Idempotency UNIQUE `(actor_id, operation, key)`; lưu hash canonical body, resource ID và response đủ replay, TTL tối thiểu 24 giờ. Webhook receipt UNIQUE `(platform, account_id, event_id)` lưu bền vững; Redis chỉ là cache.
- Outbox có ID duy nhất, trạng thái pending/sent, số lần thử và thời điểm thử lại. Không xóa dữ liệu nhận thành công khi queue/provider lỗi.

## 4. Đơn hàng và tồn kho

| Từ → đến | Tác động |
| --- | --- |
| tạo → PENDING | Snapshot tên/giá từ DB; kiểm tra product active, variant hợp lệ, đủ số lượng hiện tại; không giữ/trừ kho |
| PENDING → CONFIRMED | Lock order và các variant; kiểm tra stock>=quantity; trừ stock, ghi DEDUCT, tăng version |
| PENDING → CANCELLED | Không biến động kho |
| CONFIRMED → SHIPPING | Không biến động kho |
| SHIPPING → COMPLETED | Không biến động kho |
| CONFIRMED/SHIPPING → CANCELLED | Hoàn đúng lượng đã trừ, ghi RESTORE một lần |

Các chuyển khác trả `409 INVALID_TRANSITION`. Đơn `COMPLETED`/`CANCELLED` kết thúc. Không có API xóa đơn; hủy bằng PATCH status. Lặp lại request cùng idempotency key trả response cũ; key mới với version cũ trả `409 VERSION_CONFLICT`.

Tạo/sửa/xác nhận/hủy: lock order (nếu có), lock variant theo thứ tự UUID tăng dần; kiểm tra version rồi ghi toàn bộ trong transaction. Riêng mutation từ AI phải khóa conversation và kiểm expected_generation trước lock order, theo thứ tự conversation → order → variants. Deadlock retry hữu hạn với cùng key, không lặp side effect bên ngoài. Thiếu kho trả `409 INSUFFICIENT_STOCK`, rollback cả đơn lẫn kho. Hai đơn chờ có thể cùng tham chiếu hàng cuối; chỉ một đơn xác nhận thành công.

Chỉ sửa nội dung khi `PENDING`, yêu cầu `expected_version`. Khi thay items: merge variant trùng, dùng giá snapshot cho variant đã có, giá catalog hiện tại cho variant mới; không tự đổi giá dòng cũ khi chỉ sửa địa chỉ/số lượng. AI cập nhật qua order-service, không ghi SQL theo output model. Sửa đơn và publish event sau commit. Gửi tóm tắt khách sau khi cập nhật thành công; gửi lỗi không rollback đơn đã commit.

## 5. Tin nhắn, webhook và realtime

- Nhận webhook: xác minh chữ ký trên raw body → ghi receipt + payload cần thiết + outbox bền vững trong transaction → ACK. DB không lưu được trả 503 để provider retry; payload không hợp lệ trả 400, chữ ký sai 403. Không ACK chỉ vì đã set Redis key.
- Receipt trùng không tạo message/task/đơn mới. Worker outbox upsert customer/conversation/message idempotently; lưu message incoming là `SENT`, rồi schedule AI nếu `AI_HANDLING`. Không gọi LLM trong request webhook.
- Outgoing POST tạo message `SENDING`; chỉ `SENT` sau provider xác nhận nhận yêu cầu, không đồng nghĩa khách đã đọc. Provider reject → `FAILED`; không mất text. Retry dùng cùng message ID qua endpoint retry, không tạo bubble khác.
- Timeout kết quả gửi không rõ: không tự retry mù gây gửi trùng; reconcile theo khả năng provider, hoặc thông báo chưa xác định và cho người bán xử lý. Không cam kết exactly-once delivery bên ngoài khi provider không hỗ trợ idempotency.
- Sự kiện phát sau commit. Redis Pub/Sub không lưu lịch sử; reconnect phải tải lại API. Dedupe theo event ID/message ID. Sự kiện không thay thế DB.

## 6. AI và tiếp quản

Worker xử lý tuần tự mỗi hội thoại (lock có token sở hữu + lease), dedupe theo incoming message ID. Chụp conversation version khi bắt đầu, kiểm tra lại `ai_status`, version và deadline ngay trước ghi hành động/gửi. Tin khách mới hoặc đổi quyền AI tăng ai_generation; thao tác chỉ đánh dấu đã đọc không tăng generation. Người bán tắt AI tăng version và generation; kết quả worker cũ không được gửi.

Chỉ đề xuất action có schema; backend xác thực variant, stock, số lượng và quyền hành động. Không bịa catalog, tài khoản ngân hàng hoặc xác nhận đơn. `needs_human`, lỗi parse/provider, deadline 30 giây từ nhận tin hoặc unknown intent → `NEEDS_SELLER`, không gửi output lỗi tới khách. Timeout thu thập thông tin 1–72 giờ (mặc định 24) là cơ chế riêng: `status=NEW`, reset context, không tạo đơn, AI sẵn sàng.

Với retry kỹ thuật, tổng thời gian vẫn trong deadline 30 giây, không gửi nhiều câu trả lời cho một message. Trước EXT-01, dùng fixture có nhãn local/simulated; không ghi là đã chạy Gemini thật.

## 7. Phiên đăng nhập và cấu hình

RS256; private key chỉ auth-service đọc, public key dùng verify. Claims `sub`, `sid`, `jti`, `iat`, `exp`, issuer/audience được kiểm tra. Access 900 giây, refresh tối đa 604800 giây, idle 86400 giây. Redis lưu hash refresh và session TTL; refresh rotation nguyên tử. Logout revoke sid và blacklist jti hiện tại, đóng socket; token cũ không còn truy cập dữ liệu dù chưa hết exp. Auth/blacklist storage lỗi thì fail closed 503, không bypass.

Refresh cookie `sc_refresh`, HttpOnly, SameSite=Lax, Path `/api/v1/auth`; Secure=true trên HTTPS, dev localhost HTTP được cấu hình false. Access chỉ trong memory, không localStorage. UI khởi động gọi refresh; request credentials được cấu hình cùng allowlist CORS cụ thể. Auth endpoints dùng cookie kiểm tra Origin allowlist; GET không thay đổi phiên nghiệp vụ. Refresh/logout không cần access còn hạn. Không trả refresh token trong JSON. Không log password, token, private key hoặc toàn bộ payload chứa thông tin khách.

Chỉ một người bán: khởi tạo bằng CLI seed đọc env, hash mật khẩu, không có register công khai, không tạo lại tài khoản/mật khẩu khi restart. Seed idempotent; dữ liệu demo chỉ ở local/test, không tự gửi tin đến khách thật.
