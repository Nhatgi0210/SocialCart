# BOOT-01 / DATA-01 — kiểm chứng nền tảng

Ngày 2026-11-10. Phạm vi: runtime, schema/migration, seed và health;
không triển khai nghiệp vụ, UI mới hoặc React Native.

## Môi trường tái lập

- Python 3.11.18 (`.python-version`), Node 24.14.0 (`.node-version`), npm 11.9.0.
- MySQL 8.0.44, Redis 7.4.7; hai Compose pin cả patch và digest.
- `backend/requirements-dev.lock.txt` khóa môi trường backend + validator tài liệu
  đã kiểm trên Windows/Python 3.11; không phải lock worker Linux/WSL2 đã kiểm.
- `.venv` đã chuyển sang Python 3.11; bản cũ được giữ tại `.cache/venv312-backup`.
  Node portable tại `.cache/toolchain/node-v24.14.0-win-x64`.
  Dot-source `. .\scripts\use-local-toolchain.ps1` để chọn toolchain cho terminal.
  Script chỉ thay PATH/PYTHONUTF8 của terminal hiện tại.

## Cách chạy lại

Tạo `.venv` bằng Python 3.11.18; nếu dùng uv: `uv venv --python 3.11.18 .venv`.
Cài dependencies bằng `uv pip install --python .venv/Scripts/python.exe -r backend/requirements-dev.lock.txt`
hoặc pip của virtualenv. Với Node, dùng bản 24.14.0 từ nodejs.org hoặc version manager.

Tạo file ignored `.cache/boot.env` với `SC_VERIFY_MYSQL_PASSWORD` ngẫu nhiên chỉ dùng cho DB test.
Giữ nguyên password này khi volume test đã có. Từ root:

```powershell
docker compose --env-file .cache/boot.env -p socialcart-verify -f docker-compose.verify.yml up -d --wait --wait-timeout 150
.\.venv\Scripts\python.exe -X utf8 scripts/verify-foundation.py
.\.venv\Scripts\python.exe -X utf8 scripts/validate-docs.py
git diff --check
```

MySQL test chỉ expose 127.0.0.1:13306, Redis test 127.0.0.1:16379/15.
Runner tạo hai database UUID mới: `socialcart_test_*` và `socialcart_*_migration_test`;
không dùng DATABASE_URL ứng dụng. Giữ schema/fixture test để kiểm tra sau chạy,
không DROP DATABASE/FLUSHDB. Mỗi lần chạy tạo schema mới, không tái dùng DB có dữ liệu.
Integration auth dùng MySQL/Redis thật nhưng HTTP proxy qua ASGI; không chứng minh browser E2E.

Ứng dụng dùng Compose chính ở 3306/6379 với `.env` riêng. Wamp đang dừng;
không bật Wamp và Docker MySQL cùng port 3306. Database/volume Wamp không bị sửa/xóa.
Để dừng hạ tầng test mà giữ dữ liệu:

```powershell
docker compose --env-file .cache/boot.env -p socialcart-verify -f docker-compose.verify.yml stop
```

## Rà soát schema với contract

Migration mới `0003_contract_fields` nối tiếp `0002`, không sửa lịch sử migration đã bàn giao.
Trước upgrade database có dữ liệu: backup; sửa dữ liệu tổng đơn bằng 0 hoặc đơn trỏ sai khách
nếu có, vì constraint mới sẽ từ chối chúng. Không tự sửa/xóa dữ liệu để migration pass.

- Message.error_code/delivery_unknown: lưu lỗi và kết quả gửi chưa rõ theo OpenAPI.
- Variant.low_stock_threshold: integer không âm; baseline/backfill 0, không tự thêm cảnh báo ngoài contract.
- FAQ.trigger_keywords: JSON array; bản ghi cũ backfill `[]`; question tăng từ 500 lên 1000 theo spec.
- Conversation.ai_context: JSON nullable phục vụ internal contract, không đồng nghĩa AI worker đã có.
- Order.total_amount: tối thiểu 1 như OpenAPI; FK ghép conversation/customer ngăn liên kết sai khách.
- Customer.name ánh xạ display_name; Order.customer_name/phone_number/address ánh xạ shipping_*;
  OrderItem.product_name/variant_name ánh xạ snapshot. Các service tương lai phải serialize đúng tên API.
- Product.total_stock, OrderItem.subtotal và last_message_preview là dữ liệu tính/query,
  không sao chép thành schema độc lập. AiConfig vẫn là key/value cho timeout/payment_template.
- Webhook receipt.created_at là thời điểm server nhận/persist; worker tương lai không được lấy
  timestamp provider để reset deadline. Outbox/AI workflow và transaction kho còn phải nghiệm thu
  trong RT/WEBHOOK/AI/ORDER; schema pass không chứng minh nghiệp vụ đã chạy.

## Kiểm tra bắt buộc

Kết quả ngày 2026-11-10: **51 backend tests PASS, 0 SKIP** trên Python 3.11.18/MySQL 8.0.44/Redis 7.4.7;
**16 frontend tests PASS** cùng npm ci/lint/typecheck/build trên Node 24.14.0/npm 11.9.0.
Health qua TCP của Gateway/auth **200**; các ca DB/Redis lỗi **503** được kiểm qua HTTP ASGI
với dependency network thật. SQL offline và docs validator/diff check PASS.
Đã migrate DB ứng dụng Docker tới 0003, chưa seed người bán ứng dụng; không có browser E2E.

Runner chạy toàn bộ backend tests, gồm migration DB rỗng, dữ liệu user/FAQ cũ qua nâng cấp,
downgrade/upgrade trên schema thử, seed seller/catalog hai lần, giữ nguyên hash/password,
schema đủ 17 bảng ứng dụng, InnoDB, UTC, unique/FK/check và health DB/Redis lỗi.
Kết quả thực chạy được cập nhật trong project-status; không suy PASS chỉ từ việc có test.

## Đóng gói commit

Một commit `fix(boot): verify Python 3.11 foundation and align MySQL schema` bao gồm
toolchain/Compose, migration/model, lỗi Settings đọc dotenv, tests/runner và tài liệu.
Đừng stage `.env`, keys, cache, volume hoặc thay đổi AGENTS/karpathy-guidelines có từ trước task này.
Xem `git diff --cached --stat` trước commit; push branch để người cùng làm review.
