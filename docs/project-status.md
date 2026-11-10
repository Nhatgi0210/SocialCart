# Trạng thái dự án SocialCart

## AUTH-01 / AUTH-02 — browser local 2026-11-10

Luồng React → Gateway → Auth → MySQL/Redis đã chạy bằng trình duyệt Chromium thật.
Xem [auth-verification](auth-verification.md) để phân biệt browser, ASGI và clock test.

- Dùng lại bốn API AUTH-01. Bổ sung Web Locks cho cookie shared giữa tab,
  BroadcastChannel logout, kiểm `/me` khi focus và dialog xác nhận đăng xuất.
  Không truyền token qua channel/storage; logout gửi Bearer để server blacklist jti hiện tại.
- Sửa runtime pool_pre_ping bằng pin PyMySQL 1.1.1; cả integration auth/foundation
  bật pre-ping để không bỏ lọt lỗi checkout lần hai. Seed đóng pool đúng vòng đời.
- Browser PASS: protected deep link, sai/đúng password, `/me`, reload giữ phiên,
  hai tab refresh đồng thời, hủy/xác nhận logout, hai tab về login, cookie xóa,
  access cũ 401, 401→refresh→retry thành công, Redis down→error→retry phục hồi.
- Browser xác nhận HttpOnly/Lax/Path `/api/v1/auth` và browser storage rỗng;
  Secure=false chỉ cho HTTP dev. Seller local từ MySQL; credentials trong `.env` ignored.
- Backend: **51 PASS, 0 SKIP**, 23.83s qua verify-foundation trên MySQL8/Redis7 thật,
  có login/me/rotation/logout/revoke, seed và health. Frontend **21 tests PASS**,
  lint/typecheck/build PASS; bundle warning 511.77 kB. Validator tài liệu và diff check PASS.

Core auth web/M0 đã có bằng chứng local xuyên suốt; chưa nghiệm thu Dashboard nghiệp vụ,
provider hoặc native. AUTH-02 logout/disconnect socket còn phụ thuộc RT-01 chưa triển khai.
Không gộp trạng thái này thành DONE toàn sản phẩm hay AC-29 Dashboard đầy đủ.

## BOOT-01 / DATA-01 — kiểm chứng 2026-11-10

Kết quả mới nhất cho nền tảng local; các báo cáo phía dưới giữ bằng chứng lịch sử.
Python **3.11.18**, Node **24.14.0**, npm **11.9.0**, MySQL **8.0.44**, Redis **7.4.7**.
Đã tạo `.venv` 3.11, khóa dependencies Windows và image digest; tách Compose kiểm thử
13306/16379 với Compose ứng dụng 3306/6379. Wamp đang dừng, dữ liệu Wamp không sửa/xóa.

- `.venv/Scripts/python.exe -X utf8 scripts/verify-foundation.py -o faulthandler_timeout=30`:
  **51 PASS, 0 SKIP**, 26.33s. MySQL/Redis thật: auth integration, migration rỗng,
  nâng cấp user/FAQ cũ, backfill/downgrade/upgrade, seed seller/catalog lặp, giữ hash/password,
  17 bảng ứng dụng InnoDB, UTC, unique/FK/check và health 200/503. HTTP integration qua ASGI.
- Node 24.14.0: `npm ci --no-audit`, lint, typecheck, **16 frontend tests**, build PASS;
  bundle warning 503.66 kB như trước. Không chạy audit hay visual/browser E2E trong task này.
- Compose ứng dụng healthy; `alembic upgrade head` thật tới **0003_contract_fields**.
  Start M0 bằng script, GET qua TCP 8000/8001 đều **200**; sau đó đã dừng hai service.
- MySQL8 Docker `socialcart_db` mới chưa seed người bán/catalog; fixture seed chỉ trong DB test.
  Keys đã tạo local, không commit. MySQL/Redis ứng dụng vẫn chạy; hạ tầng test đã stop
  để giảm tài nguyên, không xóa schema/volume.
- `validate-docs.py`, SQL offline đến head và `git diff --check`: **PASS**.
- Sửa lỗi Settings: literal duration đọc được chuỗi `.env` nhưng vẫn từ chối giá trị trái baseline.
- Bổ sung migration `0003` và model theo contract: message error/delivery_unknown,
  variant threshold, FAQ keywords/question length, ai_context, tổng đơn >0,
  FK đảm bảo đơn/hội thoại cùng customer. Không đổi HTTP contract và không sửa migration cũ.

BOOT-01 và baseline schema DATA-01 đã có kiểm chứng local theo phạm vi trên.
Các transaction tồn kho/concurrency, outbox/AI workflow vẫn thuộc task nghiệp vụ tương ứng.
**M0 chưa hoàn tất** vì chưa kiểm browser auth E2E; AUTH-02/logout nhiều tab/socket còn việc.
Chi tiết nguồn, giới hạn, cách chạy lại và commit: [foundation-verification](foundation-verification.md).

Ngày kiểm tra: **2026-11-09, Asia/Saigon**. AUTH-01 bắt đầu trên `8b8ce99`, sau đó đồng bộ hai commit GitHub tới `eeff99a` trước bàn giao. Giữ migration/name và kế hoạch React Native đã có trên remote; không thêm migration trùng. Báo cáo phân biệt code với hành vi đã được kiểm chứng; không thay nghiệm thu của người dùng. Bằng chứng 2026-11-05/2026-10-30 được giữ bên dưới.

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

## Hiện trạng theo task

| Task | Trạng thái | Bằng chứng / phần còn thiếu |
| --- | --- | --- |
| DOC-01 | Có baseline | PRD, Feature Spec, data rules, contracts, kế hoạch và validator đã có |
| BOOT-01 | LOCAL BASELINE PASS (2026-11-10) | Python 3.11.18/MySQL 8.0.44/Redis 7.4.7, lock/digest, migration/seed/health thật; xem cập nhật mới nhất |
| BOOT-02 | LOCAL CHECKS PASS / VISUAL NOT RUN | React 18/TypeScript/Vite/MUI 5; theme Concept B; router, Axios/Query/Zustand, memory token, refresh single-flight và loading/error/retry. Cài từ lockfile, lint/typecheck/16 tests/build pass; chưa nghiệm thu visual |
| AUTH-01 | LOCAL MYSQL/REDIS INTEGRATION PASS (2026-11-10) | HTTP ASGI với MySQL/Redis thật; chưa browser E2E |
| AUTH-02 | CORE WEB BROWSER PASS (2026-11-10) | Chromium + MySQL/Redis thật; logout nhiều tab/refresh/revoke/recovery pass; socket disconnect chờ RT-01, Dashboard shell |
| DATA-01 | LOCAL SCHEMA CHECKS PASS (2026-11-10) | Migration 0003, backfill/rollback/seed/constraints thật; transaction kho và workflow nghiệm thu trong task nghiệp vụ |
| Các task nghiệp vụ, RT/AI/provider | NOT IMPLEMENTED | Frontend chỉ có placeholder, không có dữ liệu hay số liệu giả |
| UX-01 | NOT RUN | Chưa nghiệm thu P4.5; việc chọn Concept B không thay thế review runtime |

**M0 chưa hoàn tất.** Chưa có bằng chứng auth với MySQL/Redis thật hoặc provider live; bằng chứng migration MySQL 9.1 trước đó không thay kiểm baseline MySQL 8.

## AUTH-01 — bằng chứng ngày 2026-11-09

- `backend/auth-service/app/main.py`: bốn endpoint auth; access 900s; refresh cookie HttpOnly/Lax, Path `/api/v1/auth`, Secure theo cấu hình; kiểm Origin bắt buộc; lỗi sai email/password/inactive giống nhau; không trả refresh trong JSON; response không cache.
- `backend/shared/auth.py`: verify RS256 với đầy đủ claims; Redis lưu SHA-256 refresh, rotation nguyên tử bằng Lua, session tối đa 7 ngày và idle 24h; hoạt động đã xác thực cập nhật idle. Logout xóa sid, blacklist jti hiện tại khi có access hợp lệ; mọi access của sid bị chặn. Socket disconnect còn phụ thuộc RT-01.
- Gateway kiểm phiên trước khi proxy API được bảo vệ, Redis lỗi trả 503; chặn route ngoài map và prefix giả; bỏ header identity giả; giữ raw webhook bytes/signature và nhiều Set-Cookie. Chưa triển khai provider webhook.
- Dùng nguyên migration `0002_user_name` và model/name từ commit remote; không thay schema/migration trong AUTH-01. Seed giữ `SEED_SELLER_NAME` mặc định `Seller`, dùng Argon2id, không trim password và không thay password đã tồn tại. Login tương thích hash bcrypt cũ.
- Dependency auth khóa PyJWT 2.14.0, cryptography 50.0.2, argon2-cffi 25.1.0, bcrypt 5.0.0, email-validator 2.3.0; test fakeredis[lua] 2.32.1. Tham khảo [PyJWT RS256/claims](https://pyjwt.readthedocs.io/en/latest/usage.html), [Argon2 API](https://argon2-cffi.readthedocs.io/en/stable/howto.html), [Redis Lua atomicity](https://redis.io/docs/latest/develop/programmability/eval-intro/). Chưa audit toàn bộ dependency backend.

| Lệnh | Kết quả / giới hạn |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider` | 47 PASS, 2 SKIP (thiếu URLs cho integration auth/migration); Python 3.13.3, RSA thật, Lua trong fakeredis, DB mock. Có health hai service độc lập, login/me/refresh/logout qua Gateway, concurrent refresh, replay, idle/max age, revoke/blacklist, Origin/CORS, DB/Redis lỗi, seed idempotency và SQL offline |
| `.\.venv\Scripts\python.exe -X utf8 -m alembic -c backend/shared/db/alembic.ini upgrade head --sql` | PASS — sinh SQL tới `0002`; **không thực thi lên MySQL**. INI comments đổi ASCII để đọc được trên Windows; `-X utf8` cần cho SQL Unicode khi redirect |
| `npm.cmd --prefix frontend run lint`, `run typecheck`, `run test -- --run`, `run build` | PASS — 16 tests; build còn warning bundle 503.66 kB. Không đổi frontend, không chạy npm ci lại |
| `docker version`, `py -0p` | BLOCKED — daemon không có pipe docker_engine; launcher không phát hiện Python 3.11; venv hiện tại Python 3.13.3 |

Test integration mới ở `backend/tests/test_auth_integration.py`, chỉ chạy khi có MySQL database `socialcart_test_*` và Redis DB 15 được dành riêng. Tự upgrade Alembic, tạo seller riêng, kiểm auth/rotation/revoke qua Gateway ASGI; không phải browser E2E. Không DROP/FLUSHDB; chỉ xóa seller/session của test. Hướng dẫn ở [setup](setup.md). Lượt này không chạy integration/migration online; Docker image patch/digest và visual QA còn thiếu.

## Phạm vi thay đổi BOOT-02 (lịch sử 2026-10-30)

- `frontend/`: manifest/lockfile, cấu hình Vite/TypeScript/ESLint/Vitest; `src/components`, `pages`, `services`, `stores`, `theme`, `types` và tests.
- `.node-version`: Node 24.14.0; `.gitignore`: bỏ qua npm cache local.
- README, AGENTS, setup, implementation plan, technical design, test plan và skill local setup được sửa để không còn báo sai rằng chưa có scaffold.
- Không đổi HTTP contract, schema hay migration. API client dùng đúng OpenAPI đã có; tất cả HTTP qua Gateway `/api/v1`, cookie credentials, access token chỉ trong memory.
- Login về `/dashboard` nhưng chỉ hiển thị shell/người bán và trang chờ. Không coi đây là Dashboard nghiệm thu AC-29. Lỗi logout giữ phiên hiện tại và cho thử lại vì server chưa xác nhận revoke.

## Môi trường và giới hạn BOOT-02 (lịch sử 2026-10-30)

Windows/PowerShell; Python global và `.venv` đều **3.13.3**, chưa có Python 3.11 được launcher phát hiện. Node **24.14.0**, npm **11.9.0**. Docker CLI có mặt nhưng daemon không kết nối được qua `docker_engine`; chưa chạy Compose, migration hoặc seed. Không đọc hay sử dụng credential nền tảng.

Frontend giữ React 18/MUI 5 theo baseline. Vite 7 và Node 24 được khóa; yêu cầu Node được đối chiếu với [Vite guide](https://vite.dev/guide/), peer dependency React/Emotion theo [MUI 5 installation](https://v5.mui.com/material-ui/getting-started/installation/). Phiên bản dependency exact ở `frontend/package.json`, dependency gián tiếp ở lockfile.

## Lệnh và kết quả BOOT-02 (lịch sử 2026-10-30)

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

1. AUTH-02: kiểm browser UI→Gateway→auth→MySQL/Redis, refresh/logout/revoke; M0 chưa hoàn tất.
2. CUST-01/INBOX-01 và PROD-01 sau khi auth UI được kiểm chứng; giữ dữ liệu demo có nhãn.
3. ORDER-01 kiểm transaction kho/concurrency; RT-01 kiểm socket/reconnect/logout.
4. React Native theo MOB-01/MOB-02 sau khi chốt Expo/CLI và nền tảng; không suy auth browser thành native.
