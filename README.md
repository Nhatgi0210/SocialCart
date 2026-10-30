# SocialCart

Hệ thống quản lý tin nhắn Facebook Page/Zalo OA và hỗ trợ chốt đơn cho một hộ kinh doanh. AI tư vấn và tạo/sửa đơn chờ xác nhận; người bán xác nhận đơn.

## Hiện trạng

Ngày 2026-10-30: có tài liệu, Concept B, prototype tĩnh và scaffold backend BOOT-01 (Gateway/auth shell, model/migration chung, Compose, scripts). Frontend BOOT-02 có React 18/TypeScript/MUI 5, router bảo vệ phiên, API client và auth shell. Các trang nghiệp vụ đang là placeholder; backend chưa có login/refresh/logout/me. M0 chưa hoàn tất. Xem [trạng thái và bằng chứng](docs/project-status.md); prototype chưa có nghiệm thu P4.5.

V1: Unified Inbox, khách hàng/notes, catalog đa biến thể, đơn hàng/lifecycle, FAQ/AI/handoff, kết nối nền tảng và Dashboard. Một người bán, một Page, một OA. Không Zalo cá nhân/staff/multi-tenant/payment gateway/shipping integration. PENDING không giữ kho; xác nhận trừ kho, hủy đơn đã xác nhận hoàn kho một lần.

## Bắt đầu

Xem [AGENTS.md](AGENTS.md) cho AI coding và [setup](docs/setup.md) cho local. Chạy prototype hiện tại:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory prototype
```

Mở http://127.0.0.1:5500. Mock account ở prototype/mock-data.js, state reset sau reload. Frontend ứng dụng chạy bằng `npm.cmd --prefix frontend ci` rồi `npm.cmd --prefix frontend run dev`; hướng dẫn và giới hạn ở [setup](docs/setup.md). Bước tiếp theo: hoàn tất kiểm chứng BOOT-01 trên Python 3.11/MySQL/Redis và triển khai AUTH-01. `.env.example` chỉ là mẫu, không có secret thật.

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
