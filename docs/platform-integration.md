# Cấu hình và kết nối nền tảng

Ngày đối chiếu tài liệu chính thức **2026-11-18**. Người dùng hiện chưa có App/Page/OA
test hoặc callback HTTPS. CFG-01 có thể dùng với MySQL local. INT-01, FB-01 và ZALO-01
cần chạy thêm OAuth, nhận/gửi bằng tài khoản test để nghiệm thu live.

## Chạy local

MySQL và Redis cần đang chạy. Trong PowerShell ở thư mục gốc:

```powershell
. .\scripts\use-local-toolchain.ps1
python -X utf8 -m alembic -c backend/shared/db/alembic.ini upgrade head
.\scripts\stop-services.ps1
.\scripts\start-services.ps1 -Milestone M3
npm.cmd --prefix frontend run dev
```

M3 bật các service của M2 cùng ai-service :8006 (cấu hình), webhook-service :8007
và platform-service :8010. Worker outbox chạy trong lifespan của service tương ứng.
Worker AI/Celery sẽ triển khai theo AI-01, AI-02.

Mở `http://localhost:5173/settings` để thêm/sửa/xóa FAQ, đổi timeout thu thập đơn
từ 1 đến 72 giờ và lưu thông tin ngân hàng. Bỏ trống cả ba trường ngân hàng để gỡ
template. Các giá trị này được lưu MySQL. Việc áp dụng timeout vào luồng AI theo AI-02.

Ô trả lời trong Hội thoại gửi văn bản tối đa 2000 ký tự. Server lưu SENDING,
tiếp quản AI và ghi outbox trước khi gọi nền tảng. Khi chưa kết nối Page/OA,
tin chuyển FAILED và giữ nội dung. Sau khi kết nối, có thể **Thử gửi lại** bằng cùng
message ID. Trường hợp DELIVERY_UNKNOWN cần kiểm tra tin trên nền tảng trước khi
gửi tin mới. Refresh trang giữ dữ liệu tin và trạng thái đã lưu.

## Cấu hình dùng chung

Điền trực tiếp `.env` local theo `.env.example`. Chạy lệnh sau để kiểm tên biến còn thiếu:

```powershell
python -X utf8 scripts/check-integrations.py
```

- `ENCRYPTION_KEY` gồm 64 ký tự hex. Có thể tạo bằng
  `python -c "import secrets; print(secrets.token_hex(32))"` rồi chép vào file local.
  AES-256-GCM mã hóa token trước khi lưu MySQL. Giữ khóa này để đọc token đã lưu.
- `INTERNAL_SERVICE_TOKEN` là chuỗi ngẫu nhiên dùng chung cho call nội bộ. Tạo
  bằng `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- `PUBLIC_API_URL` là URL Gateway có HTTPS nhận được từ provider. Chạy
  `ngrok http 8000` để lấy URL, ghi đúng URL đó vào file và dashboard provider.
- `FRONTEND_URL` là URL frontend cố định để callback đưa trình duyệt về Cài đặt.
  Giữ `CORS_ALLOWED_ORIGINS` khớp frontend. Sau khi đổi backend env, khởi động lại service.

HTTP UI tiếp tục đi Gateway. Callback OAuth công khai, dùng state 10 phút,
chỉ một lần và kiểm lại phiên seller khởi tạo. Token provider được lưu mã hóa
và response kết nối chỉ trả metadata. Script start tắt access log để tránh log
authorization code trong query của callback.

## Facebook Page

Chuẩn bị Meta App, một Page test, tài khoản có quyền nhắn tin trên Page và vai trò
test trong App. Người dùng ngoài vai trò App cần điều kiện App Review tương ứng.
Kiểm quyền `pages_show_list`, `pages_messaging`, `pages_manage_metadata` và tác vụ
Page. Adapter chỉ chọn đúng `FB_PAGE_ID` đã cấu hình rồi đăng ký các sự kiện tin nhắn.
[Meta Page Webhooks](https://developers.facebook.com/docs/graph-api/webhooks/getting-started/webhooks-for-pages),
[Meta Quick Start](https://developers.facebook.com/docs/messenger-platform/getting-started/quick-start).

Điền `FB_APP_ID`, `FB_APP_SECRET`, `FB_PAGE_ID`, `FB_GRAPH_VERSION` và
`FB_WEBHOOK_VERIFY_TOKEN`, sau đó đặt `FACEBOOK_ENABLED=true`.
Chọn Graph version đúng phiên bản đang hỗ trợ trong App dashboard, dạng `vNN.0`.
Đăng ký hai URL với domain Gateway thực tế:

- OAuth `<PUBLIC_API_URL>/api/v1/connections/facebook/oauth/callback`.
- Webhook `<PUBLIC_API_URL>/webhooks/facebook`, verify token khớp file local,
  subscribe trường `messages` và `messaging_postbacks`.

Meta GET verify nhận original challenge. POST xác minh HMAC SHA-256 trên raw bytes
bằng App Secret và header `X-Hub-Signature-256`. Gửi văn bản dùng Page Messages
với `messaging_type=RESPONSE`, tuân theo cửa sổ trả lời của nền tảng.
[Meta webhook validation](https://developers.facebook.com/docs/graph-api/webhooks/getting-started/),
[Meta Page Messages](https://developers.facebook.com/docs/graph-api/reference/page/messages).

## Zalo Official Account

Chuẩn bị App, một OA test và tài khoản admin OA. Xin quyền gửi tin, quản lý tin nhắn,
nhận sự kiện tin nhắn và xem thông tin OA. Trong Developers, tạo đường dẫn cấp quyền
OAuth v4 có PKCE. Điền `ZALO_AUTHORIZATION_URL` bằng link được cấp với các vị trí động
`{state}`, `{code_challenge}`, `{redirect_uri}` và `{app_id}` nếu có trong link.
Backend chỉ chấp nhận link HTTPS thuộc `oauth.zaloapp.com`. Xác minh link thật trong
App dashboard trước khi bật adapter.
[Zalo OAuth v4](https://stc-developers.zdn.vn/docs/v2/official-account/bat-dau/xac-thuc-va-uy-quyen-cho-ung-dung-new).

Điền `ZALO_APP_ID`, `ZALO_APP_SECRET`, `ZALO_OA_ID`, `ZALO_WEBHOOK_SECRET` rồi
đặt `ZALO_ENABLED=true`. Đăng ký callback
`<PUBLIC_API_URL>/api/v1/connections/zalo/oauth/callback` và webhook
`<PUBLIC_API_URL>/webhooks/zalo`. Callback đổi code và kiểm OA qua API thông tin OA.
Backend lấy hạn token từ response. Refresh được serialize và ghi trạng thái trước
khi gọi vì refresh token chỉ dùng một lần. Nếu kết quả refresh không xác định,
Cài đặt hiển thị yêu cầu kết nối lại.
[Zalo OAuth v4](https://stc-developers.zdn.vn/docs/v2/official-account/bat-dau/xac-thuc-va-uy-quyen-cho-ung-dung-new),
[Zalo OA identity](https://stc-developers.zdn.vn/docs/v2/official-account/quan-ly/quan-ly-thong-tin-oa/lay-thong-tin-zalo-official-account).

Webhook Zalo kiểm `X-ZEvent-Signature` bằng SHA-256 của App ID + raw JSON +
timestamp + OA secret, so sánh constant-time. Tin văn bản đọc `user_send_text`,
`message.msg_id`, sender và recipient OA. Tin đính kèm được lưu dưới dạng dòng
thông báo trong Inbox, raw payload vẫn nằm trong receipt để xử lý về sau.
Gửi tư vấn qua `/v3.0/oa/message/cs`, lấy message ID từ response accepted.
Header chữ ký và payload thật còn cần đối chiếu khi có OA test.
[Zalo incoming events](https://stc-developers.zdn.vn/docs/v2/official-account/webhook/tin-nhan/su-kien-nguoi-dung-gui-tin-nhan),
[Zalo consultation API](https://stc-developers.zdn.vn/docs/v2/official-account/tin-nhan/tin-tu-van/gui-tin-tu-van-trich-dan).

## Gemini

`GEMINI_MODEL` tiếp tục để trống đến khi xác minh model truy cập được bằng key
của dự án. Khi đã chọn model, điền key/model rồi chạy
`python -X utf8 scripts/check-integrations.py --check-gemini` để kiểm metadata.
Structured output, độ trễ và chi phí cần smoke test riêng trong AI-01.
[Google model catalog](https://ai.google.dev/gemini-api/docs/models).

## Dữ liệu, retry và nghiệm thu

Migration `0007_platform_delivery` bổ sung metadata lỗi kết nối, ràng buộc một
connection mỗi nền tảng, liên kết receipt/job và bảng `platform_dispatches`.
Migration từ chối dữ liệu cũ có nhiều connection trên cùng nền tảng để người dùng chọn
account cần giữ trước khi nâng schema.

Webhook chỉ ACK sau khi receipt và job commit. Unique key chặn nhận trùng và
incoming endpoint chặn tạo message/customer/conversation trùng. Worker gọi lại với
cùng provider message ID sau lỗi nội bộ. Lỗi hạ tầng giữ job pending và thử lại có
giãn nhịp. Nền tảng bị ngắt kết nối giữ lịch sử và xóa token đã lưu.

Mỗi lần gửi có claim bền vững trước khi gọi ra provider. Timeout hoặc crash sau
claim giữ trạng thái không xác định, ngăn blind retry. Chỉ provider acceptance
mới chuyển tin thành SENT. Nền tảng từ chối lưu FAILED, cho người bán thử lại.
Các lỗi mở kết nối chắc chắn chưa gửi được tự thử tối đa ba lần.

Khi có tài khoản test, cần ghi bằng chứng cho từng nền tảng:

1. OAuth đúng account, thiếu quyền bị từ chối, state dùng lại thất bại.
2. Gửi từ tài khoản test tới Page/OA, xuất hiện trên Inbox trong 60 giây.
3. Trả lời từ UI tới tài khoản test, kiểm message ID/provider accepted.
4. Replay cùng webhook, giữ một message. Chặn sai chữ ký và sai account.
5. Ngắt service nội bộ/Redis, khôi phục và đối chiếu DB sau retry/reconnect.
6. Thử token hết hạn, refresh, disconnect và reconnect, rồi kiểm mobile web.

Các test local mô phỏng provider tách riêng trong `test_platform_pipeline.py` và
`test_provider_adapters.py`. Chúng kiểm persistence bằng MySQL/Redis và HTTP mock,
không xác nhận App đã được cấp quyền hay đã trao đổi tin thật.
