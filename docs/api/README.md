# Hợp đồng API SocialCart V1

Phiên bản 1.0.0, baseline thiết kế **2026-10-19**, chưa có server implementation. [openapi.yaml](openapi.yaml) là nguồn HTTP public cho frontend và công cụ; [service-contracts.md](service-contracts.md) mô tả API nội bộ, outbox và Socket.IO. Không duy trì một bản JSON schema thủ công khác trong frontend; sinh types/client từ spec khi BOOT-02.

## Quy ước client

- Spec dùng server `http://localhost:8000`, mọi path nghiệp vụ đã gồm `/api/v1`. UI dùng `VITE_API_URL=http://localhost:8000/api/v1` và path tương đối `/auth/login`, `/orders`, không ghép `/api/v1` hai lần.
- UUID/string ID, enum UPPER_CASE, UTC RFC 3339, tiền nguyên VNĐ. Pagination `{success,data,meta:{page,limit,total}}`; danh sách rỗng là `data:[]`, không 404. Messages trả thứ tự `created_at,id` tăng dần, conversation giảm dần `last_message_at,id`.
- Error `{success:false,error:{code,message,details}}`. Phân biệt 400 malformed, 401 unauthenticated, 403 origin/signature/quyền, 404 missing, 409 conflict, 422 validation, 429 rate limited, 502 provider rejected, 503 dependency unavailable. Không expose stack/secret. `details` là danh sách object tùy mã lỗi, không để client parse chuỗi message.
- Business endpoints dùng Bearer access. Login/refresh/logout theo cookie `sc_refresh` trong data-rules; spec security của refresh/logout là cookie, không yêu cầu access còn hạn. Login/refresh trả access JSON, refresh chỉ qua Set-Cookie. Login/refresh/logout kiểm Origin allowlist; logout cookie thiếu có thể trả 204 để UI xóa phiên local nhưng không được coi là revoke một phiên khác.
- `Idempotency-Key` bắt buộc với tạo đơn, gửi tin và retry tin, cũng như status/edit đơn. Reuse key cùng body trả response gốc (kể cả status HTTP); key khác body trả `409 IDEMPOTENCY_CONFLICT`. Kết quả transient trước commit không cache vĩnh viễn; TTL ít nhất 24h. `expected_version` ngăn sửa trạng thái/đơn dựa trên dữ liệu cũ.
- POST message trả 202 với message `SENDING`, không chứng minh provider đã nhận. Theo dõi bằng GET/event; retry message `FAILED` qua endpoint retry, không POST message mới. Trường hợp provider timeout kết quả không rõ xem data-rules, không tự gửi lặp.
- Chỉ người bán được gọi API public. `created_by` và `sender` do server gán, không nhận client tự nhận là AI/CUSTOMER. Internal principal riêng cho worker, không dùng token người bán lâu dài.

## Phạm vi bổ sung so với catalog TDD cũ

Đã cụ thể hóa các hành vi có sẵn: PATCH read thay side effect GET, POST retry message, PATCH pending order để đáp ứng FR-22c, POST upload ảnh để đáp ứng quản lý sản phẩm. Không thêm register, delete order, payment gateway, shipping integration hay VietQR endpoint. TDD đã có upload ảnh ở §11 nhưng thiếu trong catalog.

Webhook path trong spec chỉ mô tả ACK, xác minh và raw payload boundary. Payload/permission/token của nhà cung cấp phải được xác minh trong INT-01; spec không giả định ví dụ Zalo cũ là schema đầy đủ. OAuth callback trả redirect về UI, không trả token platform cho browser.

## Ví dụ công việc và lỗi

Đơn hai sản phẩm dùng UUID variant và quantity, server tính giá. Confirm `PENDING` với `expected_version=1`: thành công trả `CONFIRMED`, version 2; thiếu hàng trả `409 INSUFFICIENT_STOCK`, không đổi kho/đơn. Người bán tắt AI: PATCH ai-status `SELLER_HANDLING`; worker cũ bị fence theo ai_generation.

Ví dụ request/response và error có trong OpenAPI. Không có secret thật; token dạng minh họa không dùng xác thực được. Có thể import spec vào Postman sau này. Chưa tạo collection/workspace/cloud mock vì chưa có API chạy; khi cần runnable assertions, sinh collection từ spec rồi giữ scripts kiểm thử trong Git, không sửa hai hợp đồng độc lập.

## Kiểm chứng

Lượt tài liệu kiểm tra parse, OpenAPI validator, reference và ví dụ schema; đây là kiểm tra contract tĩnh. `docs/test-plan.md` quy định runtime/local/simulated/live. Mỗi thay đổi API cập nhật spec trước hoặc cùng code và kiểm tra drift với FastAPI-generated OpenAPI sau khi có implementation.
