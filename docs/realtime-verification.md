# RT-01 — kiểm chứng local 2026-11-16

Core outbox/Socket.IO và client đã triển khai; transport local và client mô phỏng
đã kiểm. Browser runtime, provider và toàn M1 chưa nghiệm thu. Đối chiếu AC-09,
AC-28, T-RT-01 và phần socket T-AUTH-02. AC-27 cần DASH-01; producer tin nhắn/đơn
cần task tương ứng.

## Thay đổi

- `backend/realtime-service/app/main.py`: Socket.IO :8009, JWT/session Redis,
  room seller do server chọn, kiểm UUID/resource khi join hội thoại. Kiểm phiên
  trước khi phát và mỗi giây; guard không gia hạn idle. Redis auth lỗi đóng socket.
- `backend/shared/realtime.py`, migration `0005_realtime_outbox`: service nghiệp vụ
  ghi event cùng transaction; dispatcher khóa hàng MySQL, publish Redis rồi đánh dấu
  sent. Lỗi giữ pending, tăng attempt_count, hẹn thử lại sau 5 giây. Crash sau publish
  có thể phát lại cùng event ID. Outbox gửi nền tảng được giữ riêng.
- PATCH read/status/ai-status chỉ ghi `conversation:updated` nếu dữ liệu đổi.
  No-op và stale version không tạo event mới. Thêm query HTTP `is_read` vào OpenAPI.
  Badge nav lấy số **hội thoại chưa đọc** từ `is_read=false&limit=1`, dùng `meta.total`.
- Client dùng event để invalidate Query cache, dedupe tối đa 1000 ID/version gần nhất;
  refetch khi reconnect/focus/online/gap và khi server resubscribe Redis. Có cảnh báo
  mất realtime. Logout cleanup socket/listener; token hết hạn refresh qua HTTP,
  tối đa một refresh liên tiếp trước khi kết nối thành công.

Không thêm provider adapter, Celery workflow, native auth, order hoặc Dashboard.

## Môi trường và lệnh đã chạy

Phiên này ban đầu có `.venv` Python 3.13.3, không có `.env`, keys/cache hạ tầng của
báo cáo trước. Đã tạo Python **3.11.15** trong `.cache/python` và venv riêng
`.cache/rt-venv`, giữ nguyên `.venv`. Python 3.11.18 không có trong catalog uv dùng
ở lượt này; không đổi major/minor baseline. Node **24.14.0**, npm **11.9.0**;
MySQL **8.0.44**, Redis **7.4.7** từ Compose verify pin digest. Mật khẩu test ngẫu
nhiên nằm trong `.cache/boot.env` ignored. Không dùng database ứng dụng/khách thật.

Từ root repository:

```powershell
docker --config .cache/docker compose --env-file .cache/boot.env -p socialcart-verify -f docker-compose.verify.yml up -d --wait
.cache/rt-venv/Scripts/python.exe -X utf8 scripts/verify-foundation.py -o faulthandler_timeout=30
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend test -- --run
npm.cmd --prefix frontend run build
.cache/rt-venv/Scripts/python.exe -X utf8 scripts/validate-docs.py
git diff --check
```

`verify-foundation` tạo schema `socialcart_test_*` và `*_migration_test` mới mỗi lần,
giữ schema để xem lại; Redis test dùng DB 15. Không DROP DATABASE/FLUSHDB.
Máy khác dùng Python 3.11 với `backend/requirements-dev.lock.txt` thay đường dẫn venv
riêng. Test TCP Socket.IO thêm aiohttp/dependencies đã khóa; runtime không cần aiohttp.

## Kết quả và giới hạn

| Kiểm tra | Kết quả | Bằng chứng / giới hạn |
| --- | --- | --- |
| Backend verify-foundation | 63 PASS, 0 SKIP; 41,44s | MySQL/Redis thật; upgrade rỗng/có seed/downgrade/upgrade, 18 bảng ứng dụng + alembic_version |
| Outbox MySQL | PASS | Uncommitted/rollback không publish; Redis không truy cập được giữ pending/lịch retry; hai dispatcher chỉ một publish |
| Inbox → socket | PASS | HTTP ASGI với auth thật → MySQL/outbox → Redis → TCP/WebSocket; kiểm join UUID sai/không có resource |
| Pub/Sub recovery | PASS | Redis CLIENT KILL subscriber DB test; socket vẫn mở, nhận resync và event tiếp theo |
| Socket session | PASS | RSA thật; token sai/cũ bị từ chối, logout revoke ngắt TCP; token exp ngắn thật tự ngắt; Redis auth lỗi fail closed mô phỏng |
| Replay/unit | PASS | SQLite riêng kiểm rollback/retry/redelivery; không dùng SQLite chứng minh MySQL lock |
| Frontend | 27 PASS; lint/typecheck/build PASS | HTTP/socket mock và DOM: dedupe/gap, reconnect/focus, logout/cleanup, refresh bound, retry service và badge refetch |
| Contract/tài liệu/diff | PASS | validate-docs: 46 operations, 131 schema-valid examples, 43 AC; git diff --check |
| Browser desktop/mobile/hai tab | NOT RUN | Computer Use báo browser access host/native pipe unavailable; DOM test không thay browser |
| Provider/order/dashboard producer | NOT RUN | Chưa triển khai producer; message:new trong badge test là fixture |

Lần chạy backend cuối dùng schema `socialcart_test_c752823c5f17` và
`socialcart_c752823c5f17_migration_test`. Vite warning chunk **635,93 kB** trước gzip
(**200,62 kB** sau gzip). Backend có 9 deprecation warnings Uvicorn/websockets;
không nâng stack ngoài task. Chỉ kiểm một process realtime local; chưa kiểm nhiều node.
Pub/Sub không replay: publish không có subscriber vẫn là acceptance; dữ liệu chuẩn
tiếp tục ở MySQL và client refetch khi reconnect/resync.
Sau kiểm tra đã dừng hai container verify bằng Compose stop, giữ nguyên volume/schema.

Tham khảo triển khai: [python-socketio server](https://python-socketio.readthedocs.io/en/stable/server.html),
[Socket.IO client options](https://socket.io/docs/v4/client-options/) (đọc 2026-11-16).

## Phần tiếp theo

Chạy checklist browser hai tab trong [setup](setup.md#realtime-inbox--rt-01), kiểm
badge/cảnh báo/focus desktop và mobile web. ORDER-01 đủ phụ thuộc để làm tiếp;
producer message/order/dashboard nối helper outbox trong transaction task sở hữu.
Không đánh dấu toàn M1, AC-27 hay provider live hoàn thành từ báo cáo này.
