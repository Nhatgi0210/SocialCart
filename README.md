# SocialCart 🛒

> **Hệ thống quản lý tin nhắn và chốt đơn tự động cho hộ kinh doanh đa nền tảng**

SocialCart là giải pháp toàn diện giúp một hộ kinh doanh (single-tenant) gom toàn bộ tin nhắn từ **Facebook** (Messenger) và **Zalo** về một giao diện duy nhất (**Unified Inbox**), đồng thời tích hợp trợ lý **AI thông minh** để tự động tư vấn sản phẩm, thu thập thông tin khách hàng và chốt đơn hàng một cách nhanh chóng, chính xác.

---

## 🚀 Tính năng nổi bật

- **📥 Hộp thư hợp nhất (Unified Inbox):**
  - Quản lý tin nhắn Facebook Page và Zalo (OA / cá nhân) trên cùng một màn hình theo thời gian thực.
  - Phân loại hội thoại (Chưa đọc, Đang xử lý, Chờ AI, Cần can thiệp, Đã chốt).
  - Tự động nhận diện khách hàng quay lại qua số điện thoại hoặc ID nền tảng.

- **🤖 Trợ lý AI chốt đơn tự động:**
  - Nhận diện ý định mua hàng, hỏi đáp thông tin sản phẩm và chính sách bán hàng.
  - Tư vấn biến thể (màu sắc, kích cỡ, phân loại) theo tồn kho thực tế.
  - Tự động thu thập thông tin nhận hàng (Họ tên, SĐT, Địa chỉ) và tạo đơn hàng nháp.
  - Tạo mã QR thanh toán (VietQR) chuyển khoản tự động kèm cú pháp đơn hàng.
  - Cơ chế Human-in-the-loop: Chuyển giao mượt mà cho chủ shop khi gặp ca phức tạp hoặc khách yêu cầu gặp người thật.

- **📦 Quản lý sản phẩm & Tồn kho:**
  - Danh mục sản phẩm đa biến thể (SKU, giá bán, tồn kho riêng cho từng biến thể).
  - Khóa giữ tồn kho (inventory hold) khi tạo đơn và trừ kho khi xác nhận đơn, tránh tình trạng bán vượt tồn.

- **📑 Quản lý đơn hàng (Order Lifecycle):**
  - Quản lý vòng đời đơn hàng khép kín: *Chờ xác nhận ➔ Đã xác nhận ➔ Đang giao ➔ Hoàn thành / Đã hủy*.
  - Theo dõi chi tiết giá trị đơn hàng, phí vận chuyển và trạng thái thanh toán.

- **📊 Báo cáo & Thống kê:**
  - Dashboard trực quan: Doanh thu theo ngày/tuần/tháng, số lượng đơn chốt bởi AI vs. Người bán.

---

## 📁 Cấu trúc dự án

```text
SocialCart/
├── backend/                              # Mã nguồn backend (API, webhook, AI service)
├── frontend/                             # Mã nguồn giao diện quản trị (Dashboard, Unified Inbox)
├── docs/                                 # Tài liệu đặc tả & thiết kế hệ thống
│   ├── product-requirements.md           # Product Requirements Document (PRD v1.0)
│   └── feature-specification.md          # Đặc tả chi tiết chức năng (Feature Spec v1.0)
├── Project Brief.md                      # Định hướng và mục tiêu sơ bộ
├── Project Context.md                    # Bối cảnh bài toán và phạm vi dự án
├── .gitignore                            # Cấu hình bỏ qua tệp cho Git
└── README.md                             # Giới thiệu dự án
```

---

## 📖 Tài liệu chi tiết

Hệ thống được thiết kế và đặc tả chi tiết trong thư mục `docs/`:

1. [Product Requirements Document (PRD v1.0)](docs/product-requirements.md): Xác định mục tiêu, đối tượng người dùng, yêu cầu chức năng, yêu cầu phi chức năng và tiêu chí nghiệm thu.
2. [Feature Specification v1.0](docs/feature-specification.md): Đặc tả chi tiết từng luồng nghiệp vụ (Main Flow, Edge Cases, Business Rules, UI Elements) cho 7 phân hệ chính.

---

## 🔗 Liên kết kho lưu trữ

- **GitHub Repository:** [https://github.com/Nhatgi0210/SocialCart](https://github.com/Nhatgi0210/SocialCart)
