# Trạng thái dự án SocialCart

## Bổ sung React Native 2026-11-05 — DOCUMENTATION ONLY

Người dùng yêu cầu React Native cho môn đa nền tảng và chọn chỉ cập nhật tài liệu.
D-15 đưa mobile vào phạm vi, dùng chung backend/MySQL với web. Có [mobile-plan](mobile-plan.md)
và backlog MOB-00–05; đồng bộ PRD/Feature Spec/TDD/data-rules/setup/test plan.
Expo/Android là đề xuất chưa chốt; auth native cần contract riêng trước code.
Chưa có `mobile/`, dependency, build, test native hoặc API native. M0 chưa hoàn tất.

## Cập nhật kiểm chứng local 2026-11-05

- Sửa start/stop PowerShell: truyền PYTHONPATH thực, quote đường dẫn có khoảng trắng,
  tách stderr/stdout, đặt working directory, bỏ reload khỏi tiến trình nền và tránh biến `$PID` chỉ đọc.
- Smoke tests nạp từng service bằng module riêng và gọi HTTP health với bốn tổ hợp DB/Redis.
- Migration `0001` bỏ DROP TYPE không hợp lệ trên MySQL; chỉ định InnoDB và DATETIME(6).
  Cấu hình Alembic đọc được trên Windows locale. Migration `0002_user_name` bổ sung
  users.name, backfill dữ liệu cũ; model/seed đọc SEED_SELLER_NAME. HTTP contract không đổi.
- Tạo `socialcart_db` trên Wamp MySQL 9.1.0 tại 127.0.0.1:3306 và tài khoản ứng dụng
  chỉ có quyền trên schema này; credential nằm trong `.env` bị Git ignore.
  Có 17 bảng ứng dụng InnoDB + alembic_version, revision `0002_user_name`. Chưa seed người bán/catalog.
- Tạo `.venv` bằng Python 3.12.5, cài backend/requirements-dev.txt và scripts/requirements-docs.txt.
  Chưa xác minh Python 3.11/MySQL 8, Redis hay auth thật; M0 vẫn chưa hoàn tất.
- `pytest backend/tests -q -p no:cacheprovider`: **17 PASS** khi đặt
  SOCIALCART_MIGRATION_TEST_URL trỏ database thử mới, rỗng, hậu tố `_migration_test`.
  Có upgrade 0001 → insert user fixture → upgrade head/backfill → downgrade base → upgrade head.
  Test không dùng DATABASE_URL ứng dụng; mặc định bỏ qua integration nếu thiếu URL test.
- `scripts/validate-docs.py`: PASS (45 operations, 61 schemas, 129 examples, 43 ACs).
- Start M0 thật thành công; HTTP health cả hai port trả **503 với db=ok, redis=error**.
  Stop script dừng cả hai; không còn listener 8000/8001. Chưa có bằng chứng Redis khỏe thật.
- `git diff --check`: PASS. Frontend/browser/provider không chạy trong lượt này.

Phần dưới là báo cáo lịch sử 2026-10-30, không mô tả môi trường hiện tại.

Ngày kiểm tra: **2026-10-30, Asia/Saigon**. Nền trước thay đổi: commit `2b84d6a` (`feat(boot): scaffold BOOT-01…`), working tree sạch. Báo cáo này phân biệt code đã có với hành vi đã được kiểm chứng; không thay cho nghiệm thu của người dùng.

## Hiện trạng theo task

| Task | Trạng thái | Bằng chứng / phần còn thiếu |
| --- | --- | --- |
| DOC-01 | Có baseline | PRD, Feature Spec, data rules, contracts, kế hoạch và validator đã có |
| BOOT-01 | PARTIAL | Gateway/auth shell, 17 shared ORM models, migration `0001`, Compose, requirements và scripts đã có. 10 smoke tests pass trên Python 3.13.3; chưa đạt tiêu chí runtime Python 3.11/MySQL/Redis |
| BOOT-02 | LOCAL CHECKS PASS / VISUAL NOT RUN | React 18/TypeScript/Vite/MUI 5; theme Concept B; router, Axios/Query/Zustand, memory token, refresh single-flight và loading/error/retry. Cài từ lockfile, lint/typecheck/16 tests/build pass; chưa nghiệm thu visual |
| AUTH-01 | NOT IMPLEMENTED | Auth backend chỉ có `/health`, chưa có login/me/refresh/logout. Gateway routing hiện là scaffold, chưa thực thi JWT/session protection |
| AUTH-02 | PARTIAL, SIMULATED ONLY | Form/login/logout/bootstrap và bảo vệ route được kiểm bằng HTTP mô phỏng; chưa có backend để kiểm end-to-end, chưa đồng bộ logout nhiều tab/socket |
| DATA-01 | Chưa nghiệm thu | Model/migration được scaffold sớm trong BOOT-01; chưa xác minh constraints và upgrade trên MySQL rỗng/có seed |
| Các task nghiệp vụ, RT/AI/provider | NOT IMPLEMENTED | Frontend chỉ có placeholder, không có dữ liệu hay số liệu giả |
| UX-01 | NOT RUN | Chưa nghiệm thu P4.5; việc chọn Concept B không thay thế review runtime |

**M0 chưa hoàn tất.** Không có bằng chứng auth thật, migration thật hay provider live.

## Phạm vi thay đổi BOOT-02

- `frontend/`: manifest/lockfile, cấu hình Vite/TypeScript/ESLint/Vitest; `src/components`, `pages`, `services`, `stores`, `theme`, `types` và tests.
- `.node-version`: Node 24.14.0; `.gitignore`: bỏ qua npm cache local.
- README, AGENTS, setup, implementation plan, technical design, test plan và skill local setup được sửa để không còn báo sai rằng chưa có scaffold.
- Không đổi HTTP contract, schema hay migration. API client dùng đúng OpenAPI đã có; tất cả HTTP qua Gateway `/api/v1`, cookie credentials, access token chỉ trong memory.
- Login về `/dashboard` nhưng chỉ hiển thị shell/người bán và trang chờ. Không coi đây là Dashboard nghiệm thu AC-29. Lỗi logout giữ phiên hiện tại và cho thử lại vì server chưa xác nhận revoke.

## Môi trường và giới hạn

Windows/PowerShell; Python global và `.venv` đều **3.13.3**, chưa có Python 3.11 được launcher phát hiện. Node **24.14.0**, npm **11.9.0**. Docker CLI có mặt nhưng daemon không kết nối được qua `docker_engine`; chưa chạy Compose, migration hoặc seed. Không đọc hay sử dụng credential nền tảng.

Frontend giữ React 18/MUI 5 theo baseline. Vite 7 và Node 24 được khóa; yêu cầu Node được đối chiếu với [Vite guide](https://vite.dev/guide/), peer dependency React/Emotion theo [MUI 5 installation](https://v5.mui.com/material-ui/getting-started/installation/). Phiên bản dependency exact ở `frontend/package.json`, dependency gián tiếp ở lockfile.

## Lệnh và kết quả

Các test HTTP mô phỏng không chứng minh auth backend hoạt động. Lệnh chạy từ root, dùng virtualenv hiện có; không chạy cleanup vào DB người dùng.

| Lệnh / kiểm tra | Kết quả | Phạm vi |
| --- | --- | --- |
| `npm.cmd --prefix frontend ci --offline --cache .cache/npm --no-audit` | PASS — cài sạch 332 packages từ lockfile/cache, đầy đủ install scripts | Node 24.14.0/npm 11.9.0; cache được tạo bằng online install trước đó. Audit online chạy riêng |
| `npm.cmd --prefix frontend run lint` | PASS — không lỗi/cảnh báo ESLint | Source/config frontend |
| `npm.cmd --prefix frontend run typecheck` | PASS | TypeScript strict |
| `npm.cmd --prefix frontend run test -- --run` | PASS — 16 tests, 2 files | HTTP mô phỏng + jsdom: protected deep links, bootstrap loading/401/503/retry, login validation/lỗi/duplicate submit, shell/logout, refresh single-flight/retry hữu hạn và refresh đến muộn sau logout |
| `npm.cmd --prefix frontend run build` | PASS, có warning chunk lớn | JS khoảng 503.66 kB (gzip 164.66 kB); cần chia bundle khi mở rộng chức năng. Chưa đo NFR tải trang trong browser |
| `.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider` | PASS — 10 tests | Smoke/import trên Python 3.13.3; không có MySQL/Redis thật |
| `.\.venv\Scripts\python.exe scripts/validate-docs.py` | PASS — 45 operations, 61 schemas, 129 examples, 43 ACs truy vết | Static only; cài `scripts/requirements-docs.txt` vào `.venv` trước khi chạy |
| `docker version` | BLOCKED — daemon không chạy/kết nối được | Chưa kiểm Compose/migration/seed |
| Browser visual QA | NOT RUN | Browser access host unavailable; fallback Chrome bị Computer Use dừng vì không xác định URL đủ chắc chắn. Không có screenshot, không xác nhận desktop/mobile/keyboard/reduced-motion |
| `git diff --check` | PASS | Không có lỗi whitespace; Git chỉ nhắc chuyển LF/CRLF ở một số file đã có |
| `npm.cmd --prefix frontend audit --json --cache .cache/npm --fetch-retries=0 --fetch-timeout=10000` | 2 moderate, 0 high/critical | Audit online sau cập nhật Vitest; chi tiết và giới hạn bên dưới |

### Dependency audit

Đã thay Vitest ban đầu bằng **5.0.5**, peer-compatible với Vite 7/Node 24; loại bỏ cảnh báo critical từ bộ test. Online install sau cập nhật còn **2 moderate** trong `react-router`/`react-router-dom` 6.30.6; không có high/critical. Không coi kết quả “0 vulnerabilities” của cài offline là audit online.

Hai advisory của upstream là [redirect từ untrusted path](https://github.com/remix-run/react-router/security/advisories/GHSA-wrjc-x8rr-h8h6) và [SSR hydration deserializeErrors](https://github.com/remix-run/react-router/security/advisories/GHSA-337j-9hxr-rhxg). Shell hiện dùng các đích navigation hằng số, không dùng return URL từ query và không có SSR/hydration. Đây là giới hạn phạm vi hiện tại, không phải tuyên bố thư viện đã an toàn. npm đề xuất Router 7 để vá; baseline yêu cầu Router 6 nên chưa tự nâng major. Cần xử lý quyết định này trước khi release hoặc thêm redirect động/SSR.

## Bước tiếp theo

1. Hoàn tất BOOT-01: Python 3.11, Docker/MySQL 8/Redis 7; khóa image patch/digest; kiểm upgrade DB rỗng/có seed, seed seller idempotent và health 200/503 đúng OpenAPI. Bộ smoke test hiện tại còn import `app.main` bằng cùng tên giữa hai service nên chưa chứng minh hai health endpoint độc lập.
2. AUTH-01: triển khai backend auth/Gateway với RS256, Redis session/refresh rotation, cookie Origin, revoke/idle và integration thật; không mở dữ liệu nghiệp vụ trước khi có auth.
3. AUTH-02: kiểm UI→Gateway→auth→DB và hoàn thiện logout nhiều tab/socket khi RT-01 tồn tại; giữ Dashboard là shell cho đến DASH-01.
