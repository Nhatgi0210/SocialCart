# Kế hoạch triển khai MVP

Cập nhật **2026-10-30**. DOC-01 có baseline; BOOT-01 đã scaffold nhưng còn kiểm chứng runtime; BOOT-02 có frontend và các kiểm tra local. Chi tiết lệnh/kết quả/giới hạn ở [trạng thái dự án](project-status.md). AUTH-01 chưa triển khai; auth shell frontend chưa chứng minh AUTH-02 end-to-end. M0 chưa hoàn tất. Thứ tự là phụ thuộc kỹ thuật, không phải cam kết thời gian. FR/AC tham chiếu [PRD](product-requirements.md); quy tắc chung ở [AGENTS](../AGENTS.md).

## Các mốc bàn giao

| Mốc | Đầu ra quan sát được | Điều kiện bắt đầu |
| --- | --- | --- |
| M0 — nền tảng + auth | DB migration được, login/me/refresh/logout hoạt động từ UI qua Gateway | Không cần tài khoản nền tảng/AI |
| M1 — inbox + catalog | Xem khách/hội thoại/tin nhắn từ DB; quản lý sản phẩm, tiếp quản AI, realtime | M0; fixture local có nhãn |
| M2 — đơn hàng | Tạo/sửa/xác nhận/hủy đơn, snapshot giá, transaction kho | M1 |
| M3 — nền tảng + AI | Nhận/gửi tin Facebook và Zalo OA; FAQ, thu thập đơn, handoff | M2 và EXT-01–03 |
| M4 — demo nghiệm thu | Dashboard, UX, recovery và báo cáo bằng chứng | M3; test plan hoàn tất các kiểm tra bắt buộc |

Sprint 1 đề xuất = DOC-01, BOOT-01, BOOT-02, AUTH-01, AUTH-02. Có thể chạy UX-01 và INT-01 độc lập; không để thiếu credential chặn phần local. Chưa thực hiện provider thật thì chỉ hoàn thành phần simulated của task tương ứng.

## Backlog có thể giao cho AI

| Task | Phạm vi / tài liệu đầu vào | Phụ thuộc | FR/AC | Tiêu chí hoàn thành và kiểm tra |
| --- | --- | --- | --- | --- |
| DOC-01 | Dùng bộ tài liệu hiện tại làm baseline; đối chiếu quyết định cho task | — | D-01–14 | Không còn quyết định trái nhau trong code sắp viết; EXT/UX được ghi riêng, không giả phê duyệt |
| UX-01 | Review prototype theo `prototype-review.md`; sửa lỗi được chấp nhận | — | AC-04–09, AC-25, design brief | Có bằng chứng desktop/mobile/keyboard/reduced-motion, trạng thái mỗi check và danh sách correction; không chỉ đọc code |
| BOOT-01 | `backend/`, `backend/shared/`, Compose infra, Alembic, requirements và script PowerShell | DOC-01 | FR-33–34, D-07–09 | Python 3.11; pin dependencies; DB rỗng migrate upgrade head được; seed người bán idempotent; health lỗi dependency trả 503; không có secret trong Git |
| BOOT-02 | React 18 + TypeScript + Vite + MUI; theme Concept B; router, API client, auth shell | DOC-01 | AC-30, design brief | Lockfile commit; npm ci/lint/typecheck/build pass; route bảo vệ và empty/loading/error; khóa versions tương thích, không tự nâng major stack |
| AUTH-01 | Auth endpoints và Gateway routing theo OpenAPI; session/keys theo data-rules | BOOT-01 | FR-31–34; AC-29–32 | Password hash, login lỗi chung, /me, rotation refresh, idle timeout và revoke logout; integration MySQL/Redis; test cookie Origin/CORS/401/503 |
| AUTH-02 | Form login, memory token, bootstrap refresh, logout, redirect | AUTH-01, BOOT-02 | AC-29–32 | UI→Gateway→auth→DB; lỗi không mất email, không submit đôi; refresh không lặp vô hạn; logout tab/socket; landing Dashboard khi có DASH-01, trước đó shell chỉ nghiệm thu một phần |
| DATA-01 | Migration customer/conversation/message/product/variant/order/FAQ/outbox theo data-rules | BOOT-01 | FR-10–15, FR-23–28 | UUID/enum/unique/FK/check/index/soft delete; seed hợp lệ; upgrade DB có seed; không chạy create_all thay migration |
| CUST-01 | Customer detail/list và notes, UI context panel | DATA-01, AUTH-02 | AC-10–12b | Upsert theo platform/account/user; không ghép cross-platform; note persist sau reload; hợp đồng internal upsert có auth |
| INBOX-01 | List/detail/messages/read/status/AI toggle, UI ba vùng | CUST-01 | AC-04–09, AC-20–21, AC-28 | Sắp xếp/lọc/pagination đúng; đọc là PATCH rõ ràng; status/ai/is_read độc lập; test empty/error/loading, mobile và focus |
| RT-01 | Redis outbox dispatcher→Socket.IO, session auth, reconnect/refetch | INBOX-01 | AC-09, AC-27–28 | Event schema/version đúng; dedupe; chỉ sau DB commit; logout disconnect; mất Pub/Sub không mất dữ liệu DB |
| PROD-01 | CRUD products/variants, stock update, ảnh local; UI quản lý | DATA-01, AUTH-02 | AC-13–14c | Giá nguyên; stock không âm; xóa mềm bảo toàn đơn; hết biến thể tự inactive; upload kiểm MIME/size/path; AI đọc catalog active |
| ORDER-01 | Tạo/list/detail/PATCH pending/status; modal tạo đơn và chi tiết | INBOX-01, PROD-01 | AC-22–26 | Giá lấy DB, version/idempotency; không giữ hàng PENDING; confirm/cancel nguyên tử; test hai đơn tranh hàng cuối, lặp cancel, snapshot và stale version |
| CFG-01 | FAQ, payment template, timeout 1–72h; UI settings | AUTH-02, DATA-01 | AC-17, AC-19b, AC-21b | CRUD và validation; secret không ra UI; không cấu hình bank thì không tự tạo bank; timeout persist |
| INT-01 | Thu thập và kiểm chứng đầu vào provider theo EXT-01–03 | — | FR-01–03, FR-17 | Ghi official URL/ngày/permissions/model/payload; credential nằm local secret; thử gọi tối thiểu có kiểm soát; không suy từ ví dụ cũ |
| SEND-01 | Platform send adapter + outgoing state/retry và UI recovery | INBOX-01, INT-01 | AC-03, AC-07 | Provider reject/timeout/disconnect có trạng thái thật; same message ID khi retry; kết quả không rõ không tự retry mù |
| FB-01 | OAuth Facebook, verify challenge/signature, durable webhook, receive/send | SEND-01, RT-01, INT-01 | AC-01, AC-03, AC-10, AC-12b | Raw body giữ nguyên qua Gateway; receipt trùng tạo 1 message; lỗi DB/Redis recovery; test account→Inbox ≤60s với bằng chứng live |
| ZALO-01 | OAuth Zalo OA, token refresh theo provider hiện hành, webhook/send | SEND-01, RT-01, INT-01 | AC-02–03, AC-10, AC-12b | OA only; lưu token mã hóa; validate signature theo tài liệu hiện hành; có live evidence; không chép TTL/token format cũ |
| AI-01 | Gemini adapter, structured output, FAQ/intent và handoff | CFG-01, FB-01 hoặc ZALO-01, EXT-01 | AC-15–21b | Kết quả schema-validated; không gửi khi lỗi; deadline 30s tính từ nhận; stale worker sau takeover không gửi; test deterministic + live smoke riêng |
| AI-02 | Flow nhiều sản phẩm, khách xác nhận, tạo/sửa đơn PENDING, collection timeout | AI-01, ORDER-01 | AC-15b, AC-18, AC-19b, AC-21c–22 | Dedupe task không tạo đơn đôi; backend validate giá/kho; không confirm tự động; reset context không tạo đơn khi collection timeout |
| DASH-01 | Stats và UI Dashboard | ORDER-01, RT-01 | AC-27–29 | Số liệu theo Asia/Ho_Chi_Minh, auto refresh từ event, đối chiếu query/seed; login landing Dashboard |
| QA-01 | E2E và failure scenarios trong test-plan | Các task liên quan | Toàn bộ AC | Có báo cáo PASS/FAIL/NOT RUN/BLOCKED, chỉ rõ local/simulation/live; lỗi chặn đã sửa; không ghi simulated là live |
| DEMO-01 | Hoàn thiện setup, script, runbook demo và snapshot bằng chứng | QA-01 | NFR 60s/30s/3s | Máy sạch chạy theo setup được; backup/restore DB thử trên local; demo bằng tài khoản test; không public service nội bộ |

## Hợp đồng giao task

Một task ghi: **ID, mục tiêu, FR/AC, tài liệu cần đọc, dependency đã có, phạm vi file/service, đầu ra, cách kiểm tra**. Kết quả bàn giao gồm diff, lệnh/kết quả thực chạy, migration/contract đổi gì, hạn chế và bước tiếp theo. Task chỉ cập nhật DONE khi có bằng chứng tương ứng; task cần live có thể ghi `LOCAL PASS / LIVE BLOCKED`, không gộp thành DONE.

Ví dụ AUTH-01: dùng OpenAPI auth và data-rules §7; triển khai login/me/refresh/logout qua Gateway, migration users và seed; kiểm thử đúng/sai password, rotation, idle, token sau logout và Redis down; không làm register, staff hoặc reset password.

## Definition of Done theo mốc

- M0: lệnh setup backend/frontend được chạy thật; auth e2e và revoke pass; không cần Gemini credential.
- M1: seed không tạo dữ liệu nền tảng thật; API và UI dùng cùng enums, reload không mất notes/messages.
- M2: các test kho/concurrency dùng MySQL, không dùng SQLite thay bằng chứng lock.
- M3: hai nền tảng có bằng chứng live riêng; AI không tự xác nhận; loss/retry không mất incoming đã ACK.
- M4: người dùng xem được evidence và danh sách giới hạn; checklist prototype chưa chạy không tự đổi thành accepted.
