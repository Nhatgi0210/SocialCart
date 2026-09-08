# Project Context

## 1. Bối cảnh dự án

Dự án hướng đến việc xây dựng một hệ thống hỗ trợ **một hộ kinh doanh** quản lý tin nhắn và chốt đơn từ **Facebook và Zalo**.

Sản phẩm cần giải quyết bài toán quản lý hội thoại, thông tin khách hàng và quá trình xử lý đơn hàng trong một hệ thống thống nhất.

## 2. Mục đích sử dụng tài liệu

Tài liệu này cung cấp bối cảnh để các bước phân tích yêu cầu và thiết kế sản phẩm hiểu đúng mục tiêu, phạm vi và các quyết định của dự án.

Tài liệu không thay thế Product Requirements Document (PRD). Các yêu cầu chức năng chi tiết sẽ được xác định và phê duyệt ở bước tạo PRD.

## 3. Trạng thái dự án

**Giai đoạn:** Khởi tạo ý tưởng và xác định phạm vi sản phẩm.

**Trạng thái:** Chưa có PRD chính thức.

**Mức độ xác định:** Mục tiêu sản phẩm, nền tảng ban đầu, đối tượng sử dụng và định hướng tự động hóa đã được xác định sơ bộ.

## 4. Các quyết định đã được phê duyệt

### 4.1. Nền tảng

Phiên bản đầu tiên tập trung vào:

- **Facebook**
- **Zalo**

### 4.2. Đối tượng sử dụng

Hệ thống phục vụ **một hộ kinh doanh duy nhất**.

### 4.3. Mức độ tự động hóa

Hệ thống hướng đến việc sử dụng **AI tự xử lý và chốt đơn**.

### 4.4. Định hướng mở rộng

Sau khi hoàn thành phiên bản đầu tiên, nếu có thời gian và nguồn lực, có thể phát triển thêm:

- Các nền tảng khác.
- Hỗ trợ nhiều hộ kinh doanh.

Các nội dung mở rộng này **không thuộc phạm vi phiên bản đầu tiên**.

## 5. Mục tiêu đã xác định

- Xây dựng hệ thống quản lý tin nhắn từ Facebook và Zalo.
- Hỗ trợ AI tự động xử lý hội thoại.
- Hỗ trợ AI tư vấn sản phẩm và chốt đơn.
- Quản lý thông tin khách hàng.
- Quản lý thông tin sản phẩm.
- Quản lý trạng thái đơn hàng.
- Giảm thời gian xử lý và hạn chế bỏ sót khách hàng.

## 6. Phạm vi đã xác định sơ bộ

Sản phẩm tập trung vào:

1. Tiếp nhận và quản lý tin nhắn từ Facebook và Zalo.
2. Quản lý hội thoại.
3. Quản lý thông tin khách hàng.
4. Quản lý sản phẩm.
5. AI tự động xử lý hội thoại.
6. AI tư vấn sản phẩm.
7. AI hỗ trợ chốt đơn.
8. Quản lý trạng thái đơn hàng.

## 7. Các quyết định chưa có

### 7.1. Quy trình chốt đơn

Chưa xác định:
- Các bước chốt đơn.
- Thông tin bắt buộc của đơn hàng.
- Cách xác nhận đơn.
- Cách xử lý khi khách hàng thay đổi thông tin.
- Cách xử lý khi khách hàng không phản hồi.

### 7.2. Phạm vi AI

Chưa xác định:
- AI được phép tự xử lý những tình huống nào.
- AI có được tự xác nhận đơn hàng hay không.
- AI có được tự thay đổi thông tin đơn hàng hay không.
- Khi nào cần chuyển cho người bán.
- Cách xử lý khi AI không hiểu yêu cầu khách hàng.

### 7.3. Quản lý sản phẩm

Chưa xác định:
- Sản phẩm có biến thể hay không.
- Có quản lý tồn kho không.
- Có quản lý giá theo từng nền tảng không.
- Có đồng bộ sản phẩm từ nền tảng hay không.

### 7.4. Quản lý đơn hàng

Chưa xác định:
- Các trạng thái đơn hàng.
- Cách tạo đơn hàng.
- Cách cập nhật đơn hàng.
- Có cần tích hợp đơn vị vận chuyển hay không.

## 8. Ràng buộc và nguyên tắc

- Phiên bản đầu tiên chỉ tập trung vào Facebook và Zalo.
- Phiên bản đầu tiên phục vụ một hộ kinh doanh.
- Không tự động thêm các nền tảng hoặc tính năng mở rộng chưa được phê duyệt.
- Các yêu cầu phải mô tả hành vi sản phẩm, không chỉ mô tả công việc lập trình.
- Các chức năng AI cần có cách kiểm tra và can thiệp khi cần thiết.
- Các yêu cầu về xác thực, lưu trữ và phân quyền phải được làm rõ trong PRD.

## 9. Giả định hiện tại

Các giả định dưới đây **chưa phải quyết định chính thức**:

- Hệ thống có giao diện quản lý tập trung.
- Người bán có thể xem lịch sử hội thoại.
- Người bán có thể theo dõi trạng thái đơn hàng.
- AI có thể sử dụng thông tin sản phẩm để tư vấn khách hàng.
- AI có thể tự động xử lý các tình huống hội thoại thuộc phạm vi được xác định.
- Người bán vẫn có thể can thiệp thủ công khi cần.

## 10. Các vấn đề cần giải quyết trước khi tạo PRD

- Xác định quy trình chốt đơn.
- Xác định mức độ tự động hóa cụ thể của AI.
- Xác định các tình huống cần người bán can thiệp.
- Xác định phạm vi quản lý sản phẩm.
- Xác định phạm vi quản lý đơn hàng.
- Xác định các yêu cầu về bảo mật, lưu trữ và phân quyền.
- Xác định các tiêu chí đánh giá thành công.

## 11. Nguyên tắc cập nhật

Các quyết định mới được con người phê duyệt sẽ được bổ sung vào tài liệu này.

Khi có mâu thuẫn giữa các tài liệu, ưu tiên quyết định mới nhất đã được phê duyệt.