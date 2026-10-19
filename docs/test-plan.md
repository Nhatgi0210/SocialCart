# Kế hoạch kiểm thử và nghiệm thu

Baseline 2026-10-19. **Chưa chạy kiểm thử ứng dụng** vì chưa có implementation. Tài liệu này định nghĩa bằng chứng cần thu; kiểm tra OpenAPI/Markdown không thay cho các test bên dưới.

## 1. Môi trường và dữ liệu

- Unit cho tính tiền, validation, transition và deadline với clock kiểm soát; integration dùng **MySQL 8.0 + Redis 7** test riêng, không SQLite để chứng minh row lock.
- Frontend component bằng Vitest/Testing Library; e2e bằng Playwright sau BOOT-02, đi qua Gateway. Khi service upstream chưa có/không thể gọi thật: simulation HTTP có nhãn, inject timeout/5xx/409/429; kết quả local không được đổi tên thành live.
- Test secret/DB tách local demo, credential thật không vào fixtures. Fixture UUID cố định: 1 seller; 2 platform accounts; cùng chuỗi user ID ở FB/Zalo nhưng 2 customer; 3 conversation NEW/IN_PROGRESS/RESOLVED, 3 ai_status độc lập; message CUSTOMER/SELLER/AI và FAILED.
- Catalog: áo M giá 150000 stock10; áo L stock0; sản phẩm inactive; variant stock1 cho test đồng thời; sản phẩm đã có order để test soft delete. Notes, nhiều dòng order và timestamp hai bên mốc ngày Việt Nam.
- Seed phải idempotent, không dispatch ra nền tảng. Worker/network giả có fixture riêng không lấy token thật. Test DB migration upgrade rỗng và đã có seed; downgrade chỉ thử DB disposable, không hứa mọi data migration đảo ngược được.

## 2. Ma trận truy vết PRD

Các AC trong một hàng đều phải được kiểm tra; không suy một AC pass từ AC khác. Task ở [implementation-plan](implementation-plan.md).

| AC | Task | Bằng chứng cần có |
| --- | --- | --- |
| AC-01 | FB-01 | OAuth Page, status và tin test vào Inbox ≤60s; live riêng |
| AC-02 | ZALO-01 | OAuth OA, status và tin test ≤60s; không test cá nhân V1 |
| AC-03 | SEND-01, FB-01, ZALO-01 | Token hết/revoke: ERROR, cảnh báo, không tạo tin giả |
| AC-04, AC-05, AC-06 | INBOX-01 | Sort/filter/badge bằng seed, gồm no-result và pagination |
| AC-07 | INBOX-01, SEND-01 | Lịch sử, send thành công, reject, timeout, retry giữ text/ID |
| AC-08, AC-09 | INBOX-01, RT-01 | PATCH read và ba trạng thái AI độc lập processing status |
| AC-10, AC-11, AC-12, AC-12b | CUST-01, FB-01, ZALO-01 | Upsert unique, notes reload, history và không duplicate customer |
| AC-13, AC-13b, AC-13c | PROD-01 | CRUD, variants, last variant inactive và soft delete giữ snapshot |
| AC-14, AC-14b, AC-14c | PROD-01 | Search/filter, total stock, cập nhật và threshold badge |
| AC-15, AC-15b | AI-01, AI-02 | Grounding catalog, không bịa, hết hàng không tạo đơn |
| AC-16 | AI-01 | Deadline tính từ nhận tin; provider lỗi/parse lỗi không gửi, handoff |
| AC-17 | CFG-01, AI-01 | FAQ cấu hình persist và câu hỏi tương tự có câu trả lời đúng |
| AC-18 | AI-02 | Thu thập đúng field, nhiều items, khách xác nhận trước tạo |
| AC-19, AC-19b | AI-01, AI-02 | Unknown→handoff khác collection timeout→NEW/reset/no order |
| AC-20, AC-21 | INBOX-01, AI-01 | Tắt AI ngăn worker cũ, bật lại cho tin tiếp theo |
| AC-21b | CFG-01, AI-02 | Có/không template; nội dung đúng tổng và bank đã cấu hình |
| AC-21c | AI-02, ORDER-01 | Sửa pending persist; variant hết hàng rollback; confirmed chuyển người bán |
| AC-22, AC-22b | ORDER-01, AI-02 | Tạo 1 pending, liên kết hai chiều đúng customer/conversation |
| AC-23, AC-24, AC-24b | ORDER-01 | Filter/status, row lock, deduction/restore đúng một lần |
| AC-25, AC-26 | ORDER-01 | Tạo thủ công qua modal, required và snapshot/detail |
| AC-27, AC-28 | DASH-01, RT-01 | Stats đối chiếu DB, ngày Việt Nam, realtime badge không F5 |
| AC-29, AC-30, AC-31, AC-32 | AUTH-01, AUTH-02, DASH-01 | Login đúng/sai, landing Dashboard, API/route protection, logout revoke |

## 3. Ca lỗi và cạnh tranh bắt buộc

| ID | Setup / hành động | Kết quả yêu cầu |
| --- | --- | --- |
| T-AUTH-01 | Sai email hoặc password | Cùng lỗi chung, không có access/cookie hợp lệ |
| T-AUTH-02 | Refresh, dùng lại refresh cũ, logout rồi gọi API/socket với token cũ | Rotation nguyên tử, token cũ bị chặn, socket disconnect; không refresh loop |
| T-AUTH-03 | Giả clock idle 24h; Redis down; Origin ngoài allowlist | Session hết hạn; dependency 503 fail closed; cookie operation 403 |
| T-ORD-01 | Stock1, hai order PENDING cùng variant, confirm đồng thời | Một confirm thành công; một 409; stock0, không âm; cả hai pending trước đó không giữ kho |
| T-ORD-02 | Confirm/cancel lặp cùng key; key đổi body; version cũ | Không trừ/hoàn hai lần; idempotency conflict; version conflict |
| T-ORD-03 | Order nhiều items, một item thiếu hàng khi confirm | Rollback toàn bộ, không item nào bị trừ |
| T-ORD-04 | Đổi giá catalog, sửa địa chỉ pending, xóa mềm variant | Snapshot giá cũ giữ; history vẫn đọc được; không cascade xóa order item |
| T-ORD-05 | Shipping→cancel; completed→cancel; client gửi total/created_by | Hoàn đúng một lần; transition cuối bị chặn; input server-owned không được tin |
| T-HOOK-01 | Replay cùng event 2 lần và đồng thời, Redis restart/cache hết TTL | Một receipt/message/AI action; unique DB còn bảo vệ |
| T-HOOK-02 | Crash sau receipt trước publish; crash sau publish trước mark sent | Outbox tiếp tục; redelivery không tạo thêm side effect |
| T-HOOK-03 | Chữ ký sai/raw body đổi; DB down trước persist | 403; không tạo dữ liệu; DB down trả 503, không ACK thành công |
| T-MSG-01 | Provider 4xx/5xx/429/timeout và disconnect | Trạng thái đúng; chỉ retry hữu hạn khi an toàn; unknown delivery không tự gửi lặp |
| T-AI-01 | Gemini chậm >30s, JSON sai, ID variant bịa, bank bịa | Không gửi output lỗi; handoff; backend chặn action không hợp lệ |
| T-AI-02 | Seller tắt AI giữa lúc model đang chạy | Worker chưa claim mất quyền; không gửi reply cũ sau takeover; ghi nhận ranh giới request đã dispatch |
| T-AI-03 | Worker/task trùng; crash sau tạo order trước gửi reply | Cùng action_id không tạo order thứ hai; workflow tiếp tục từ bước persisted |
| T-AI-04 | Collection timeout 24h và timer cũ sau tin mới | Context reset chỉ khi generation/deadline còn đúng; NEW, không order, AI sẵn sàng |
| T-RT-01 | Drop socket/PubSub; reconnect; event duplicate/out of order | API refetch khôi phục, không duplicate bubble hoặc ghi đè version mới |
| T-UI-01 | 320/375/768/1440px, keyboard-only, reduced motion | Theo checklist P4.5; dialog trap/return focus, điều khiển tiếp cận được |

## 4. NFR và điều kiện nghiệm thu

Đo mốc nhận webhook, persist, UI display và provider acceptance bằng request/event IDs; không dùng thời gian bắt đầu worker thay thời gian nhận. NFR: incoming→Inbox ≤60s, incoming→AI response hoặc handoff ≤30s; trang chính ≤3s. Ghi máy/mạng/dataset/browser, số lần đo và trường hợp fail. Local latency không chứng minh provider live SLA; benchmark chưa chạy ghi NOT RUN.

M0 cần auth/migration/build; M2 bắt buộc test concurrency MySQL; M3 cần từng provider live + AI smoke, cùng simulation failure; M4 cần tất cả AC và UX review đã xử lý/ghi rủi ro. Không tạo báo cáo pass bằng cách chỉ xác nhận file tồn tại.

## 5. Mẫu báo cáo bằng chứng

Mỗi run ghi commit/diff, ngày giờ/múi giờ, môi trường và dependency versions; task/test/AC; lệnh; status `PASS / FAIL / NOT RUN / BLOCKED`; log/screenshot/report path; local/simulated/live; giới hạn và người review. Đầu vào thiếu ghi tên EXT tương ứng, không ghi secret. Không đánh dấu accepted thay người dùng.
