# AUTH-01 / AUTH-02 — kiểm chứng local 2026-11-10

Phạm vi: đăng nhập web thật qua React → Gateway → auth-service → MySQL/Redis.
Backend AUTH-01 có từ commit 02eda60; dùng lại implementation đó.
Không thêm auth native, endpoint, migration hoặc API nghiệp vụ.

## Bổ sung trong lượt này

- Dialog xác nhận logout theo Feature Spec; hủy dialog giữ phiên, lỗi server cho thử lại.
- Web Locks serialize thao tác login/refresh/logout dùng chung cookie giữa các tab.
  Single-flight trong mỗi tab và revision guard vẫn giữ, gồm refresh còn chờ lock sau remote logout.
- BroadcastChannel truyền duy nhất tín hiệu logout, không truyền token/thông tin người bán.
  Mỗi tab xóa memory; subscription hiện có xóa Query cache. Tab được focus lại gọi `/me`
  để phát hiện phiên mất hiệu lực khi đã bỏ lỡ tín hiệu. Không persist access trong browser storage.
- Logout gửi cả cookie và access trong memory để server có thể blacklist jti hiện tại.
- Khóa PyMySQL 1.1.1 trong requirements/dev lock cho bộ SQLAlchemy 2.0.36 + aiomysql 0.2.0.
  Trình duyệt thật bắt được lỗi checkout thứ hai với pool_pre_ping và PyMySQL 1.2.4;
  integration cũ tạo engine không bật pre-ping nên bỏ lọt. Nay integration bật đúng tùy chọn runtime.
- Seed đóng pool trước khi event loop kết thúc; seed seller lặp không đổi password.

Nguồn kỹ thuật: [Web Locks](https://developer.mozilla.org/en-US/docs/Web/API/Web_Locks_API),
[BroadcastChannel](https://developer.mozilla.org/en-US/docs/Web/API/Broadcast_Channel_API),
[báo cáo upstream về aiomysql pre-ping](https://github.com/sqlalchemy/sqlalchemy/discussions/13305).

## Môi trường và bằng chứng

Kiểm tra cuối: **51 backend tests PASS, 0 SKIP** (23.83s, MySQL/Redis thật),
**21 frontend tests PASS**; lint/typecheck/build, docs validator và diff check PASS.
Build còn warning chunk 511.77 kB (gzip 166.70 kB); chưa tối ưu bundle trong task auth.

Python 3.11.18, Node 24.14.0, MySQL 8.0.44 và Redis 7.4.7 Docker.
Gateway/auth chạy TCP 8000/8001; Vite ở `http://localhost:5173`.
Playwright CLI khởi tạo browser Chromium riêng, hai tab chung browser context.
Không mock HTTP trong các ca browser sau:

1. Chưa có cookie: truy cập `/inbox` → `/login`.
2. Sai mật khẩu: hiện lỗi chung, giữ email; không truy cập shell.
3. Đúng mật khẩu seller đã seed trong MySQL: vào `/dashboard` và hiện seller.
4. Reload: refresh cookie thật → giữ đăng nhập. `/me` qua API client trả 200 và đúng email DB.
5. LocalStorage/sessionStorage đều có 0 keys. Cookie có HttpOnly, SameSite=Lax,
   Path `/api/v1/auth`; Secure=false chỉ vì đang chạy dev HTTP localhost.
6. Hai tab gọi refreshSession đồng thời: cả hai thành công nhờ Web Locks.
7. Bấm logout rồi “Ở lại”: giữ shell. Xác nhận logout: cả hai tab về login;
   cookie bị xóa, access token trước logout gọi `/me` trả 401; reload vẫn ở login.
8. Thay token memory bằng chuỗi bị server từ chối để kích hoạt recovery:
   API client refresh và gọi `/me` lại thành công 200. Đây là kiểm 401/retry thật,
   không phải chờ access hết hạn 15 phút; expiry/idle/max-age dùng clock test backend.
9. Dừng Redis ứng dụng, reload khi có cookie: UI báo lỗi kiểm phiên với nút thử lại.
   Bật Redis, bấm thử lại: khôi phục shell; không bypass khi dependency lỗi.

Browser snapshots nằm local trong `.playwright-cli/` bị ignore, có thể chứa input test;
không commit/publish snapshot, token hay `.env`. Lỗi HTTP 401/503 chủ đích trong các ca lỗi
không được ghi là request thành công. Favicon 404 của scaffold không ảnh hưởng auth.

## Chạy lại

```powershell
. .\scripts\use-local-toolchain.ps1
python -m pip install -r backend/requirements-dev.lock.txt
docker compose up -d --wait mysql redis
python -X utf8 -m alembic -c backend/shared/db/alembic.ini upgrade head
python -X utf8 scripts/init-local-keys.py
python -X utf8 scripts/seed-demo.py --seller-only
.\scripts\start-services.ps1 -Milestone M0
npm.cmd --prefix frontend run dev
```

Seed dùng SEED_SELLER_EMAIL/PASSWORD/NAME trong `.env`; không dùng tài khoản prototype.
Đã tạo seller local khi DB chưa có người bán; mật khẩu ngẫu nhiên giữ trong `.env` bị ignore.
Không thay password tài khoản đã có. Kiểm browser theo checklist trên; không gọi DB từ UI.
Gọi lại unit/integration bằng các lệnh foundation-verification; đọc kết quả thực chạy trong project-status.

## Giới hạn nghiệm thu

AUTH-01 và luồng AUTH-02 web đã có local browser evidence. Dashboard vẫn là shell;
không ghi DASH-01/AC-29 đầy đủ hoặc cả sản phẩm hoàn tất. Socket.IO chưa triển khai nên
logout/disconnect socket nghiệm thu cùng RT-01; không thêm socket giả trong auth.
Web Locks/BroadcastChannel áp dụng trên trình duyệt hỗ trợ và cùng origin;
fallback không Web Locks chỉ giữ single-flight trong một tab. Chưa nghiệm thu browser cũ,
Safari/Firefox, deploy HTTPS, provider live hoặc React Native.
