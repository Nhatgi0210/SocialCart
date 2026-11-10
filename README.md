# SocialCart

Hệ thống quản lý tin nhắn Facebook Page/Zalo OA và hỗ trợ chốt đơn cho một hộ kinh doanh. AI tư vấn và tạo/sửa đơn chờ xác nhận; người bán xác nhận đơn.

## Hiện trạng

Auth web cập nhật 2026-11-10: đã kiểm trình duyệt Chromium → Gateway → Auth → MySQL/Redis,
có reload/refresh, `/me`, xác nhận logout, revoke và đồng bộ logout nhiều tab.
Xem [bằng chứng auth](docs/auth-verification.md). Socket disconnect chờ RT-01; Dashboard vẫn shell.

Nền tảng cập nhật 2026-11-10: Python 3.11.18, Node 24.14.0, MySQL 8.0.44/Redis 7.4.7
và migration `0003_contract_fields`. Bộ kiểm chứng thật, cách chọn toolchain và đóng gói commit
ở [foundation verification](docs/foundation-verification.md). Browser E2E/nghiệp vụ chưa nghiệm thu.

Bổ sung 2026-11-05: dự án có kế hoạch **web React + app React Native**, dùng chung
FastAPI Gateway và MySQL. Người dùng chọn cập nhật tài liệu trước; chưa scaffold mobile.
Expo/Android là phương án đề xuất, auth native cần chốt contract.
Xem [kế hoạch React Native](docs/mobile-plan.md) và task MOB-00–05 trong implementation-plan.

Ngày 2026-11-09: có tài liệu, Concept B, prototype, scaffold BOOT-01/02 và backend AUTH-01 (login/me/refresh/logout, RS256, session/rotation/revoke Redis, Gateway protection). Backend đã kiểm bằng HTTP mô phỏng/fakeredis; chưa chạy integration MySQL/Redis hoặc browser E2E. Frontend React 18/TypeScript/MUI 5 có router bảo vệ phiên và auth shell; các trang nghiệp vụ là placeholder. M0 chưa hoàn tất. Xem [trạng thái và bằng chứng](docs/project-status.md); prototype chưa nghiệm thu P4.5.

V1: Unified Inbox, khách hàng/notes, catalog đa biến thể, đơn hàng/lifecycle, FAQ/AI/handoff, kết nối nền tảng và Dashboard. Một người bán, một Page, một OA. Không Zalo cá nhân/staff/multi-tenant/payment gateway/shipping integration. PENDING không giữ kho; xác nhận trừ kho, hủy đơn đã xác nhận hoàn kho một lần.

## Bắt đầu

Xem [AGENTS.md](AGENTS.md) cho AI coding và [setup](docs/setup.md) cho local. Chạy prototype hiện tại:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory prototype
```

Mở http://127.0.0.1:5500. Mock account ở prototype/mock-data.js, state reset sau reload. Frontend ứng dụng chạy bằng `npm.cmd --prefix frontend ci` rồi `npm.cmd --prefix frontend run dev`; hướng dẫn và giới hạn ở [setup](docs/setup.md). Bước tiếp theo: kiểm chứng BOOT-01/AUTH-01 trên Python 3.11/MySQL/Redis và AUTH-02 qua browser. `.env.example` chỉ là mẫu, không có secret thật.

## Bản đồ tài liệu

| Tài liệu | Mục đích |
| --- | --- |
| [Decisions](docs/decisions.md) | Nguồn ưu tiên, đồng bộ mâu thuẫn và đầu vào còn thiếu |
| [PRD](docs/product-requirements.md), [Feature Spec](docs/feature-specification.md) | Phạm vi, FR/AC, flow và business rules |
| [Technical Design](docs/technical-design.md), [Data Rules](docs/data-rules.md) | Kiến trúc, schema, transaction, idempotency và auth |
| [Implementation Plan](docs/implementation-plan.md) | Mốc, task, dependency, FR/AC và Definition of Done |
| [API guide](docs/api/README.md), [OpenAPI](docs/api/openapi.yaml) | Hợp đồng public với schemas/errors/examples |
| [Service Contracts](docs/api/service-contracts.md) | Internal HTTP, outbox/AI workflow và Socket.IO |
| [Test Plan](docs/test-plan.md) | Ma trận AC, fixtures, concurrency/failure và bằng chứng |
| [Setup](docs/setup.md), [.env.example](.env.example) | Chạy được hiện tại và lệnh mục tiêu sau scaffold |
| [Design Brief](docs/product-design-brief.md), [Design Decision](docs/product-design.md) | Interaction contract và Concept B |
| [Prototype Review](docs/prototype-review.md) | Checklist P4.5, trạng thái chưa chạy và cách ghi issue |
| [Documentation Validation](docs/documentation-validation.md) | Kết quả kiểm tra bộ tài liệu; giới hạn bằng chứng |

## Cấu trúc

`docs/` tài liệu; `prototype/` demo tĩnh; `design/concepts/` các concept; `.agents/skills/` hướng dẫn theo domain. Backend mục tiêu `backend/<service>/app/`, shared model/migration `backend/shared/`, frontend React `frontend/`. Project Brief/Context giữ bối cảnh lịch sử.

Gemini 1.5 Pro trong lựa chọn cũ đã shutdown; model khả dụng cần EXT-01 trước khi tích hợp. Xem nguồn chính thức và phân loại quyết định trong TDD/decision log. Phần setup/auth không cần chờ credential AI/nền tảng.
