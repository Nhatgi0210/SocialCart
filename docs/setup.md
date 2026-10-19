# Chạy SocialCart tại local

Cập nhật 2026-10-19. **Hiện có:** prototype HTML/CSS/JS. **Chưa có:** ứng dụng backend/frontend, Compose, migrations, seed hay startup scripts. Các mục “sau BOOT” là giao diện vận hành cần được hiện thực ở task tương ứng; chưa được kiểm chứng là chạy được.

## 1. Chạy được ngay: prototype

Từ root repository, trong PowerShell:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory prototype
```

Mở `http://127.0.0.1:5500`. Tài khoản minh họa nằm trong `prototype/mock-data.js`; không dùng cho ứng dụng thật. Dữ liệu reset khi reload; không có API, DB hay Gemini thật. Dừng server bằng Ctrl+C. Hình/font ngoài có thể cần Internet.

## 2. Môi trường mục tiêu sau BOOT-01/02

| Thành phần | Baseline / cách khóa |
| --- | --- |
| Python | 3.11 theo TDD; ghi patch thực chạy trong báo cáo BOOT-01 |
| Node.js | Bản LTS còn hỗ trợ và tương thích Vite đã chọn; ghi exact version vào `.node-version` ở BOOT-02 |
| Backend | FastAPI 0.115.x, SQLAlchemy 2.x, Pydantic 2.x, Alembic; pin patch trong requirements đã kiểm thử |
| Frontend | React 18, TypeScript, MUI 5, TanStack Query 5, Zustand, Router 6; khóa bằng package-lock.json sau compatibility check |
| Hạ tầng | MySQL 8.0, Redis 7, Docker Compose v2; pin image digest/patch ở BOOT-01 |
| Worker | Celery 5.x; worker chuẩn chạy Linux/WSL2, không mặc định khẳng định Windows native được hỗ trợ |
| Tích hợp | ngrok và tài khoản test Facebook/Zalo OA; Gemini model xác minh trong INT-01 |

Không coi version đang có trên máy là version đã chốt cho dự án. Không tự thay major stack chỉ vì scaffold mặc định dùng phiên bản mới.

## 3. Cấu hình

Hiện có thể tạo cấu hình local từ mẫu:

```powershell
Copy-Item -LiteralPath '.env.example' -Destination '.env'
```

Điền DB password, keys và secrets tại local; `.env` không commit. Dùng `.env.example` làm danh mục biến chính thức. `.env` root dùng cho backend/Compose; Vite sau BOOT-02 có `envDir: '..'`, chỉ expose `VITE_*`.

JWT dùng cặp RSA key riêng; BOOT-01 phải cung cấp `scripts/init-local-keys.py` tạo `keys/private.pem` và `keys/public.pem` nếu chưa có, không ghi đè key hiện tại. `ENCRYPTION_KEY` là hex 32 bytes và không đổi khi DB còn token đã mã hóa. Seed người bán đọc `SEED_SELLER_EMAIL`/`SEED_SELLER_PASSWORD`, không in mật khẩu. Cấu hình theo service: auth không bắt buộc Gemini/Facebook/Zalo secret; chỉ adapter được bật mới yêu cầu credential tương ứng.

## 4. Khởi tạo sau BOOT-01/02

Chỉ chạy khi các file được nêu đã có. Task BOOT phải cập nhật mục này nếu giao diện lệnh thay đổi và ghi kết quả thực thi.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe scripts/init-local-keys.py
docker compose up -d mysql redis
.\.venv\Scripts\python.exe -m alembic -c backend/shared/db/alembic.ini upgrade head
.\.venv\Scripts\python.exe scripts/seed-demo.py --seller-only
npm.cmd --prefix frontend ci
```

`backend/requirements-dev.txt` là dependency dev tổng hợp các service, phải được tạo ở BOOT-01. Alembic config dùng đường dẫn tương đối với chính config; không phụ thuộc terminal đang ở thư mục shared. Seed seller-only là bắt buộc cho auth, seed catalog/conversation demo là tùy chọn và chỉ local/test.

## 5. Khởi động sau BOOT

Script mục tiêu `scripts/start-services.ps1` chạy service nền với log và PID theo từng service; trên Windows dùng tiến trình ẩn, không mở hàng loạt cửa sổ. Script hỗ trợ chọn service cho mốc đang làm và dừng đúng tiến trình do nó tạo.

Lệnh chạy một service từ root để debug:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'backend'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend/auth-service --host 127.0.0.1 --port 8001 --reload
```

Thay tên/port theo TDD. M0 cần Gateway/auth; M1/M2 thêm service liên quan, chưa cần bật tất cả 11 service. Dùng hostname `localhost` nhất quán cho UI/API/socket trong trình duyệt để refresh cookie same-site hoạt động; nếu chọn `127.0.0.1`, đổi đồng bộ VITE URLs và origin, không trộn hai hostname. Frontend:

```powershell
npm.cmd --prefix frontend run dev -- --host 127.0.0.1
```

Worker sau AI-01 chạy trong Linux/WSL2 với venv Linux riêng, từ `backend/ai-service`; đặt PYTHONPATH trỏ `backend/`, dùng `celery -A app.celery_app:celery_app worker --loglevel=info`. Không dùng venv Windows trong WSL. Connection host của DB/Redis phải thực sự truy cập được từ môi trường worker.

## 6. Webhook sau INT-01

```powershell
ngrok http 8000
```

Callback `https://<domain-được-cấp>/webhooks/facebook` và `/webhooks/zalo` qua Gateway. Không public trực tiếp DB/Redis/service nội bộ. Gateway giữ nguyên raw bytes/body/signature headers. Verify token dùng đúng `FB_WEBHOOK_VERIFY_TOKEN`. OAuth callback ở `/api/v1/connections/<platform>/oauth/callback`. Chỉ đăng ký webhook sau khi verify signature/durable receipt đã có; không dùng endpoint mô phỏng làm bằng chứng live.

## 7. Kiểm tra sau khi có implementation

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run test -- --run
npm.cmd --prefix frontend run build
git diff --check
```

BOOT-02 phải cung cấp đúng các npm script trên. Backend tests cần cấu hình DB test riêng và Redis DB test; không chạy migration cleanup vào dữ liệu demo/người dùng. Kiểm tra `/health` của service đang bật: 200 khi dependency cần thiết sẵn sàng, 503 khi chưa sẵn sàng; không lộ connection string.

Công cụ kiểm tra tài liệu đã có, độc lập ứng dụng: cài `scripts/requirements-docs.txt` vào virtualenv riêng rồi chạy `python scripts/validate-docs.py`. Nó kiểm OpenAPI/examples, link file local và truy vết AC; không chạy ứng dụng hay gọi provider.

## 8. Lỗi thường gặp và vận hành demo

| Hiện tượng | Kiểm tra |
| --- | --- |
| Thiếu manifest/Compose/migration | Task BOOT chưa làm; không coi là lỗi môi trường |
| 401 lặp | Cookie credentials, Origin/CORS, RSA public key, issuer/audience, session Redis; không loop refresh vô hạn |
| Không nhận webhook | Callback thực tế, Gateway route, signature, receipt/outbox, provider delivery log |
| Có message nhưng AI im lặng | ai_status, worker/outbox, deadline, EXT-01 và adapter flag; không bật AI ngầm |
| Socket mất cập nhật | Session/socket auth, Redis Pub/Sub, reconnect/refetch; dữ liệu DB vẫn là nguồn chuẩn |

DEMO-01 phải ghi lệnh backup/restore đã thử trên DB local, đường dẫn log, cách restart và replay outbox. Dừng app bằng script/PID hoặc Ctrl+C; `docker compose stop` giữ volume. Không dùng DROP DATABASE hay xóa volume làm bước debug mặc định. Production deploy là mốc riêng, chưa được chứng nhận bởi hướng dẫn demo này.
