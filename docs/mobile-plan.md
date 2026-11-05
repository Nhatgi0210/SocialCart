# SocialCart — kế hoạch React Native

Ngày 2026-11-05. Người dùng yêu cầu bổ sung React Native để phục vụ môn đa nền tảng,
và chọn **chỉ cập nhật kiến trúc, tài liệu, kế hoạch** trong lượt này.
Chưa có app mobile, manifest, build native hoặc nghiệm thu Android/iOS.

## 1. Mục tiêu và phạm vi

SocialCart có hai client cho cùng một người bán: web React/MUI và app React Native.
Khách hàng vẫn nhắn qua Facebook Page/Zalo OA; không cần cài app SocialCart.
Không thêm tenant, staff, database hay backend riêng cho mobile.

Đề xuất bản mobile đầu: đăng nhập/đăng xuất; Inbox và chi tiết hội thoại;
trả lời, tiếp quản AI; xem thông tin/ghi chú khách; chọn sản phẩm để tạo đơn;
xem, xác nhận và hủy đơn theo lifecycle hiện có. Dashboard hiển thị số liệu thật
khi DASH-01 đã có; trước đó chỉ có shell, chưa nghiệm thu Dashboard.
Các màn hình quản trị catalog đầy đủ, FAQ và OAuth nền tảng ưu tiên trên web.
Phân bổ màn hình này là kế hoạch đề xuất, không tuyên bố mobile đã đủ mọi tính năng web.

Thông báo push, camera/upload ảnh, biometric login, offline mutation và phát hành store
chưa nằm trong đợt mobile đầu. Realtime khi mở app không đồng nghĩa push khi app đóng.
Không tự mở rộng sang thanh toán/vận chuyển hoặc Zalo cá nhân.

## 2. Kiến trúc dùng chung backend

```text
Web: frontend/ (React + TypeScript + MUI)
Mobile dự kiến: mobile/ (React Native + TypeScript)
        | HTTP nghiệp vụ /api/v1
        v
API Gateway :8000 -> các service FastAPI -> MySQL dùng chung
        |
Web và mobile -> realtime-service :8009 (Socket.IO riêng)
```

Mobile không truy cập MySQL/Redis, endpoint internal, Gemini hoặc token Facebook/Zalo trực tiếp.
Server vẫn sở hữu giá, tồn kho, trạng thái đơn, quyền AI, idempotency và transaction.
PENDING không giữ kho; xác nhận/hủy cập nhật trạng thái và kho nguyên tử như web.

React Native dùng View/Text/Pressable và navigation native; không tái sử dụng MUI/DOM/CSS
bằng cách copy component web. Giữ màu sắc và ngôn ngữ Concept B nhưng thiết kế lại bố cục:
Inbox list → chat → thông tin khách, nút Back, bàn phím, safe area và màn hình tạo đơn.

Có thể chia sẻ TypeScript types sinh từ OpenAPI, formatter VNĐ/UTC và validation thuần.
HTTP transport, lưu phiên, navigation và component theo từng client. Chỉ tách package chung
khi có code thực sự cần dùng chung; không sao chép một bộ schema nghiệp vụ mới sang mobile.
React của mobile theo cặp Expo/React Native được kiểm chứng khi scaffold; không nâng React 18 của web theo mobile.

## 3. Lựa chọn công cụ còn cần chốt

- **Đề xuất:** Expo + TypeScript, ưu tiên demo Android trên Windows; chọn navigation khi scaffold.
- Nếu môn học bắt buộc React Native CLI hoặc native module đặc thù, chọn workflow tương ứng trước MOB-01.
- Chưa chốt Android-only hay cả Android/iOS, Expo SDK, React Native version hoặc thiết bị demo.
- MOB-01 kiểm Node/SDK/React compatibility từ tài liệu chính thức, pin dependency và commit lockfile riêng.
- Build iOS local cần môi trường macOS/Xcode; việc dùng cloud build phải được lựa chọn riêng.

Nguồn đối chiếu ngày 2026-11-05:
[React Native framework setup](https://reactnative.dev/docs/environment-setup),
[Expo project creation](https://docs.expo.dev/more/create-expo/),
[React Native environment](https://reactnative.dev/docs/set-up-your-environment).
Các trang theo phiên bản hiện hành có thể thay đổi; không dùng chúng làm bằng chứng app đã chạy.

## 4. Auth mobile — chốt contract trước implementation

Auth OpenAPI hiện tại dành cho browser: access token trong memory, refresh HttpOnly cookie,
Origin allowlist và rotation/revoke. Không giả định app native dùng được nguyên cơ chế này,
không bỏ kiểm Origin của endpoint web để chữa lỗi mobile.

**Phương án đề xuất cho MOB-02:** auth native riêng dưới Gateway, access trong memory,
refresh opaque lưu secure storage của OS; cùng kiểm mật khẩu, RS256, session Redis,
TTL/idle/rotation/revoke như web. Nếu dùng Expo, có thể dùng
[SecureStore](https://docs.expo.dev/versions/latest/sdk/securestore/).
Không lưu password/refresh trong AsyncStorage, log, URL hay biến public.

Chưa chốt path/request/response native và phạm vi revoke giữa các thiết bị.
MOB-02 phải quyết định rõ: web/app có phiên riêng ra sao; logout phiên hiện tại hay toàn bộ;
bootstrap/refresh khi mất mạng, lỗi ghi secure storage và request refresh đến muộn sau logout.
Không nhận diện client tin cậy chỉ bằng header do client gửi. Không coi việc thiếu Origin
là chứng minh request từ app native.

Trước khi code login mobile: cập nhật OpenAPI, ví dụ, data-rules, service-contracts và tests
cùng thay đổi; bảo đảm endpoint web không trả refresh token trong JSON. Contract hiện tại
chưa được sửa và không có endpoint native nào hoạt động trong lượt tài liệu này.

## 5. Đồng bộ dữ liệu và vòng đời app

- Dùng cùng UUID, enum, tiền nguyên VNĐ và RFC 3339 UTC; hiển thị giờ Việt Nam.
- App đang mở nhận invalidation qua Socket.IO rồi refetch API, không lấy socket làm DB.
- Khi foreground/reconnect: kiểm phiên và refetch để bù sự kiện bỏ lỡ lúc background.
- Web/app sửa cùng đơn: gửi expected_version; 409 phải tải lại và cho người bán xem dữ liệu mới.
- Mutation dùng Idempotency-Key theo OpenAPI; retry giữ key và body. Không tự gửi lại mutation
  có kết quả chưa rõ, không tự xếp hàng xác nhận đơn offline.
- Khi mất mạng: hiển thị trạng thái và giữ bản nháp trong phiên nếu phù hợp; không báo gửi thành công giả.
- Logout/phiên bị thu hồi: xóa token/cache theo contract đã chốt và ngắt socket tương ứng.
- App không giữ token nền tảng; Facebook/Zalo và AI chạy hoàn toàn ở backend.

## 6. Kết nối local

Workbench chỉ là công cụ xem/quản trị MySQL; app luôn gọi Gateway.
`localhost` trên điện thoại không phải PC chạy backend. Với Android Emulator chuẩn,
kiểm cấu hình host (thường 10.0.2.2); với máy thật dùng địa chỉ LAN hoặc HTTPS dev endpoint.
Gateway hiện bind loopback; khi kiểm máy thật cần cấu hình bind/firewall có chủ đích cho Gateway,
không expose MySQL/Redis/các service nội bộ. Không đổi script hiện tại chỉ để chuẩn bị mobile.

Nếu dùng Expo: dự kiến `mobile/.env` với EXPO_PUBLIC_API_URL gồm `/api/v1`
và EXPO_PUBLIC_SOCKET_URL trỏ realtime riêng. Đây đều là URL công khai, không phải secret.
[Expo environment variables](https://docs.expo.dev/guides/environment-variables/)
được nhúng vào bundle; không đặt credential trong EXPO_PUBLIC_*.
Chỉ ghi lệnh chạy thực tế trong setup sau khi có manifest.

## 7. Thứ tự thực hiện và bằng chứng

1. MOB-00: kế hoạch và ranh giới (lượt tài liệu này).
2. MOB-01: chốt yêu cầu môn học/thiết bị, scaffold và navigation shell.
3. MOB-02: auth native contract + backend + UI tích hợp; phụ thuộc AUTH-01.
4. MOB-03: Inbox/khách/realtime; phụ thuộc các API nghiệp vụ và RT-01/SEND-01 tương ứng.
5. MOB-04: đơn hàng/catalog đọc và Dashboard; phụ thuộc ORDER-01/PROD-01/DASH-01.
6. MOB-05: demo web và mobile trên cùng dữ liệu, thiết bị/emulator và kiểm failure scenarios.

M0 backend/auth vẫn là ưu tiên; có thể làm shell mobile độc lập nhưng không dùng mock login
để ghi AUTH/MOB-02 hoàn tất. Có thể chia hai người: backend/contracts và web/mobile UI,
review chéo payload và cùng kiểm luồng tích hợp. Không cam kết thời gian khi chưa biết deadline môn học.

Checklist nghiệm thu mobile nằm trong test-plan; task/dependency nằm trong implementation-plan.
Bundle/typecheck pass không thay việc mở app Android/iOS. Bằng chứng phải phân loại
static, simulated, emulator/device và live provider; chỉ tuyên bố nền tảng đã kiểm chứng.
