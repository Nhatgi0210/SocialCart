# SocialCart — hướng dẫn làm việc với repository

## Hiện trạng và phạm vi

Repository hiện có tài liệu và prototype tĩnh. `backend/` và `frontend/` chưa có ứng dụng. Không mô tả endpoint, migration, script hay kiểm thử là đã chạy nếu chưa có bằng chứng thực thi.

V1 phục vụ một người bán, một Facebook Page và một Zalo OA. Không thêm staff, multi-tenant, Zalo cá nhân, cổng thanh toán hay tích hợp vận chuyển. AI chỉ tạo/sửa đơn `PENDING`; người bán xác nhận đơn.

## Đọc tài liệu theo nhiệm vụ

1. [Quyết định và nguồn ưu tiên](docs/decisions.md): đọc trước khi xử lý mâu thuẫn.
2. [Kế hoạch triển khai](docs/implementation-plan.md): chọn task và xem phụ thuộc, FR/AC, tiêu chí hoàn thành.
3. [PRD](docs/product-requirements.md), [Feature Spec](docs/feature-specification.md): hành vi và nghiệm thu.
4. [Thiết kế kỹ thuật](docs/technical-design.md), [quy tắc dữ liệu](docs/data-rules.md): kiến trúc và bất biến nghiệp vụ.
5. [OpenAPI](docs/api/openapi.yaml): hợp đồng HTTP; [sự kiện và API nội bộ](docs/api/service-contracts.md): giao tiếp giữa service.
6. [Product design](docs/product-design.md), [design brief](docs/product-design-brief.md): giao diện và tương tác; prototype chỉ minh họa, không phải logic backend.
7. [Setup](docs/setup.md), [test plan](docs/test-plan.md): cách chạy và kiểm chứng.

Chỉ đọc thêm các mục/skill liên quan. Các skill trong `.agents/skills/` là hướng dẫn áp dụng; không được thay thế quyết định nghiệp vụ trong tài liệu trên. Chỉ thị trực tiếp của người dùng được ưu tiên. Nếu có mâu thuẫn chưa được giải quyết trong decision log, nêu rõ điểm cần quyết định và tiếp tục phần độc lập; không tự ghi rằng người dùng đã phê duyệt.

## Quy ước triển khai

- Giữ Microservices Lite, MySQL dùng chung, Redis/Celery, FastAPI, React + TypeScript + MUI. Thư mục chuẩn: `backend/<service-name>/app/`, `backend/shared/`, `frontend/src/`.
- Tất cả HTTP từ UI qua Gateway `/api/v1`; Socket.IO kết nối realtime-service riêng. Webhook công khai qua Gateway `/webhooks/*` và xác minh chữ ký tại webhook-service.
- ID UUID dạng chuỗi; tiền là số nguyên VNĐ; thời gian API RFC 3339 UTC. Enum, transaction và trạng thái theo `data-rules.md`.
- Không giữ hàng khi tạo đơn `PENDING`. Xác nhận/hủy đơn cập nhật tồn kho và trạng thái trong cùng transaction.
- Không sao chép schema giữa service; chia sẻ model/migration trong `backend/shared/`. Ngoại lệ transaction tồn kho được ghi rõ trong `data-rules.md`.
- Migration bằng Alembic; không dùng `Base.metadata.create_all()` lúc khởi động ứng dụng để thay migration.
- Không commit `.env`, private key, token nền tảng hay dữ liệu khách hàng thật. `.env.example` chỉ chứa cấu hình mẫu; biến `VITE_*` không chứa secret.
- API thay đổi thì cập nhật OpenAPI, ví dụ và kiểm thử liên quan cùng thay đổi đó. Chi tiết bổ sung năm 2026-10-19 là baseline kỹ thuật, chưa phải bằng chứng hệ thống đã hoạt động.

## Nhịp làm việc và hoàn thành task

Làm từng task có kết quả kiểm chứng được. Giữ diff đúng phạm vi, không sửa việc của người dùng. Báo giả định ảnh hưởng hành vi trước khi thực hiện phần phụ thuộc.

Một task code hoàn thành khi: hành vi đúng FR/AC; schema/migration tương thích; xử lý lỗi liên quan; kiểm tra phù hợp đã chạy; tài liệu bị ảnh hưởng được cập nhật. Báo file thay đổi, lệnh chạy, kết quả và phần chưa kiểm chứng. Không đánh dấu cả milestone hoàn tất chỉ vì đã scaffold.

Lệnh **hiện dùng được**: `python -m http.server 5500 --bind 127.0.0.1 --directory prototype` để xem prototype; `git diff --check` để kiểm tra diff; `python scripts/validate-docs.py` sau khi cài `scripts/requirements-docs.txt` để kiểm tra contract/tài liệu. Lệnh backend/frontend mục tiêu và điều kiện áp dụng ở `docs/setup.md`; chưa có manifest thì không tuyên bố build/test ứng dụng đã pass.
