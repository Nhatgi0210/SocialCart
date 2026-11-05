# Database local

`init.sql` chỉ tạo schema `socialcart_db`, không xóa database có sẵn.
Chạy file này trong MySQL Workbench nếu thiết lập trên máy mới, sau đó điền
`DATABASE_URL` trong `.env` (không commit credential) và chạy từ root:

```powershell
.\.venv\Scripts\python.exe -m alembic -c backend/shared/db/alembic.ini upgrade head
```

Alembic là nguồn duy nhất tạo/cập nhật bảng; không import bản SQL bảng riêng.
Trong Workbench, bấm Refresh cạnh SCHEMAS, mở `socialcart_db` → Tables.
Schema có 17 bảng ứng dụng và bảng `alembic_version`.

Ngày 2026-11-05 đã tạo và migrate trên MySQL Wamp 9.1.0 tại 127.0.0.1:3306.
Các bảng ứng dụng dùng InnoDB/utf8mb4 và thời gian DATETIME(6).
Chưa seed dữ liệu bán hàng hay người bán. Muốn seed người bán, đặt
`SEED_SELLER_NAME`, `SEED_SELLER_EMAIL`, `SEED_SELLER_PASSWORD` trong `.env`,
sau đó chạy `scripts/seed-demo.py --seller-only` bằng Python virtualenv.
