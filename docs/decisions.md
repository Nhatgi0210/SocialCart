# Quyết định triển khai SocialCart

Ngày đồng bộ: **2026-10-19**. Đây là bản đối chiếu tài liệu và baseline kỹ thuật để bắt đầu code; không tạo thêm phê duyệt của người dùng.

## Nguồn quyết định

Chỉ thị trực tiếp hiện tại → quyết định sản phẩm/kỹ thuật đã được người dùng phê duyệt mới nhất → PRD/Feature Spec đã đồng bộ → hợp đồng và quy tắc triển khai. Quyết định kỹ thuật không được âm thầm mở rộng phạm vi sản phẩm. Skill, ví dụ code và prototype phải theo các nguồn này. `Project Brief.md` và `Project Context.md` là bối cảnh lịch sử.

| ID | Nội dung thống nhất | Cơ sở / phân loại |
| --- | --- | --- |
| D-01 | V1: Facebook Page + Zalo OA; Zalo cá nhân ngoài V1 | TD-12 trong TDD mới hơn OQ-06 của PRD; đồng bộ lại PRD/Feature Spec |
| D-02 | `PENDING` không giữ/trừ kho. `CONFIRMED` trừ; hủy từ `CONFIRMED`/`SHIPPING` hoàn kho một lần | Feature Spec §7.2 và PRD FR-25b; loại bỏ hướng dẫn giữ hàng tự thêm trong skill/README |
| D-03 | UUID dạng chuỗi cho ID; mã đơn hiển thị riêng; tiền nguyên VNĐ | TDD §4, TD-13; không dùng ID integer/Decimal từ ví dụ skill |
| D-04 | JWT RS256, access 15 phút, refresh tối đa 7 ngày; revoke khi logout; idle timeout 24 giờ | TDD §10 + PRD §6.2. Idle là giới hạn phiên, không phải TTL access token |
| D-05 | Tách `status`, `ai_status`, `is_read` | TDD §4 và design brief; không gộp thành một enum |
| D-06 | Concept B: Outfit, nền sáng ấm, teal AI, cam handoff | Product Design, quyết định đã ghi ngày 2026-09-24; thay theme minh họa cũ |
| D-07 | Microservices Lite, 11 service, một DB MySQL | TDD TD-01–03; không đổi sang monolith |
| D-08 | `backend/<service>/app/`; `backend/shared/db/` quản lý model/migration tập trung; `frontend/src/services/`, `stores/` | Quy ước kỹ thuật mới để khớp thư mục backend đã tồn tại; thay tên `services/` cấp root trong sơ đồ cũ |
| D-09 | API `/api/v1`, socket riêng :8009; ngrok trỏ Gateway :8000 cho webhook | Baseline routing để có một callback URL; Gateway giữ nguyên body/header chữ ký |
| D-10 | Refresh cookie HttpOnly; access token trong bộ nhớ; kiểm tra Origin cho auth dùng cookie | Baseline kỹ thuật mới, chi tiết trong `data-rules.md`; thay localStorage trong ví dụ skill |
| D-11 | Tạo/sửa/xác nhận đơn và biến động kho dùng transaction MySQL chung; khóa hàng theo thứ tự ID | Baseline kỹ thuật cho D-02. Ngoại lệ có giới hạn đối với quyền ghi bảng giữa order/product |
| D-12 | Hợp đồng HTTP ở OpenAPI; sự kiện/API nội bộ ở service-contracts; task/test truy vết FR/AC | Baseline tài liệu, chưa có runtime |
| D-13 | Timeout thu thập đơn: reset context, `status=NEW`, AI sẵn sàng; không tạo đơn | PRD FR-20b + Feature Spec §6.7; khác timeout/lỗi kỹ thuật AI vốn chuyển `NEEDS_SELLER` |
| D-14 | Landing sau login là Dashboard trong sản phẩm; prototype vào Inbox để minh họa | PRD AC-29. Trước khi Dashboard được làm, Sprint 1 có thể dùng trang shell hiển thị người dùng; chưa đủ AC-29 toàn phần |

## Những điểm còn phụ thuộc đầu vào/thực thi

| ID | Cần xác nhận bằng gì | Chặn task nào |
| --- | --- | --- |
| EXT-01 | Model Gemini Pro khả dụng với tài khoản, structured output, chi phí/độ trễ; không mặc định model 1.5 từ tài liệu cũ | INT-01, AI-01; không chặn setup/auth/inbox |
| EXT-02 | Facebook app, Page, quyền và tài khoản test, callback/verify token | INT-01, FB-01 live |
| EXT-03 | Zalo OA, app, quyền, callback và mẫu payload/chữ ký chính thức hiện hành | INT-01, ZALO-01 live |
| UX-01 | P4.5 kiểm tra bằng trình duyệt và người dùng chấp nhận các correction | UX-01; không giả mạo kết quả audit |
| TOOL-01 | Chốt patch version và lockfile khi scaffold, chạy trên Python 3.11 + Node LTS phù hợp Vite đã chọn | BOOT-01/02 |

Google ghi Gemini 1.5 Pro đã shutdown ngày 2025-09-29 trong [changelog chính thức](https://ai.google.dev/gemini-api/docs/changelog#september-29-2025), được đọc ngày 2026-10-19. Lịch sử lựa chọn được giữ trong TDD; `.env.example` để `GEMINI_MODEL` trống cho đến EXT-01. Không tự chuyển sang nhà cung cấp khác hoặc model khác rồi ghi là người dùng đã chọn. Nguồn cần kiểm tra lại ở thời điểm tích hợp: [Google model deprecations](https://ai.google.dev/gemini-api/docs/deprecations), [model catalog](https://ai.google.dev/gemini-api/docs/models), [Facebook Messenger](https://developers.facebook.com/docs/messenger-platform/), [Zalo OA](https://developers.zalo.me/docs/official-account/).

## Quy tắc cập nhật

Mỗi thay đổi quyết định ghi ngày, cơ sở, phạm vi ảnh hưởng và task/test liên quan. Phân biệt rõ: **quyết định đã có**, **baseline kỹ thuật bổ sung**, **đầu vào chưa có**. Chỉ ghi “đã nghiệm thu/đã phê duyệt” khi có bằng chứng tương ứng.
