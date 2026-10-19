---
name: socialcart-order-flow
description: Implement/debug đơn hàng SocialCart, snapshot giá và transaction tồn kho theo lifecycle V1.
---

# SocialCart Order Lifecycle

Nguồn chuẩn: [Feature Spec §7](../../../docs/feature-specification.md), [data rules §4](../../../docs/data-rules.md), [OpenAPI](../../../docs/api/openapi.yaml).

PENDING→CONFIRMED→SHIPPING→COMPLETED; PENDING/CONFIRMED/SHIPPING có thể CANCELLED; terminal không đổi. AI chỉ tạo/sửa PENDING, seller confirm. Tạo pending không giữ/trừ stock; confirm trừ kho, cancel confirmed/shipping hoàn đúng một lần. Không có hold_quantity V1.

UUID chuỗi, order_code riêng, tiền nguyên VNĐ; không thêm shipping_fee/payment_status/VietQR endpoint từ ví dụ cũ. Snapshot item name/price từ DB; input UI/LLM không quyết định giá. Chỉ sửa nội dung PENDING; giữ snapshot variant cũ, variant mới dùng giá hiện tại.

Lock order và variants theo thứ tự ID, expected_version và Idempotency-Key theo spec; stock/order/movement ledger commit cùng transaction. Không HTTP trừ kho rồi ghi order. Thiếu kho rollback hết. Kiểm hai đơn tranh stock cuối, confirm/cancel lặp, version cũ, snapshot sau đổi giá/xóa mềm.

Hủy qua PATCH status, không DELETE order. Payment chỉ gửi thông tin bank đã cấu hình; bổ sung QR/giữ hàng cần quyết định phạm vi riêng, không suy từ README cũ.
