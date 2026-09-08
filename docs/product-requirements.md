# Product Requirements Document: Hệ Thống Quản Lý Tin Nhắn và Chốt Đơn Tự Động Cho Hộ Kinh Doanh Đa Nền Tảng

> **Trạng thái:** Approved  
> **Phiên bản:** 1.0  
> **Ngày tạo:** 2026-09-08  
> **Cập nhật lần cuối:** 2026-09-08  
> **Nguồn:** Project Brief + Project Context + Quyết định phê duyệt OQ-01 → OQ-10 + Review Gate P3.2

---

## Mục lục

1. [Overview & Context](#1-overview--context)
2. [Objectives & Success Metrics](#2-objectives--success-metrics)
3. [Scope Boundaries](#3-scope-boundaries)
4. [Functional Requirements & User Stories](#4-functional-requirements--user-stories)
5. [Observable Acceptance Criteria](#5-observable-acceptance-criteria)
6. [Technical Considerations & Non-Functional Requirements](#6-technical-considerations--non-functional-requirements)
7. [Assumptions](#7-assumptions)
8. [Decisions Log](#8-decisions-log)

---

## 1. Overview & Context

### 1.1. Background & Context

Hộ kinh doanh nhỏ bán hàng qua mạng xã hội (Facebook, Zalo) thường nhận tin nhắn từ nhiều nguồn riêng biệt. Người bán phải chuyển đổi qua lại giữa các ứng dụng, dẫn đến bỏ sót khách hàng, trả lời chậm và khó theo dõi đơn hàng.

Dự án SocialCart xây dựng một hệ thống hợp nhất: tập trung tất cả hội thoại từ Facebook và Zalo vào một nơi, đồng thời sử dụng AI để tự động xử lý hội thoại, tư vấn sản phẩm và hỗ trợ chốt đơn.

### 1.2. Problem Statement

| Vấn đề | Tác động |
|--------|---------|
| Tin nhắn phân tán trên nhiều nền tảng | Người bán mất thời gian chuyển đổi app, dễ bỏ sót |
| Phải trả lời thủ công các câu hỏi lặp | Mất thời gian, không nhất quán |
| Không có màn hình tổng quan về đơn hàng | Khó theo dõi trạng thái, dễ nhầm lẫn |
| Lịch sử khách hàng phân tán | Không có bức tranh đầy đủ về khách hàng |

### 1.3. User Personas

**Primary — Chủ hộ kinh doanh (Người bán):**
- Cá nhân hoặc hộ gia đình kinh doanh hàng hóa qua Facebook Page và Zalo OA / Zalo cá nhân.
- Không nhất thiết có kỹ năng kỹ thuật cao.
- Mong muốn: tiết kiệm thời gian, không bỏ sót đơn, kiểm soát được AI.

**Secondary — Khách hàng (ẩn danh từ góc nhìn hệ thống):**
- Người nhắn tin qua Facebook hoặc Zalo.
- Không có tài khoản trực tiếp trên hệ thống.

> [!NOTE]
> Phiên bản đầu tiên **chưa hỗ trợ nhân viên** (staff) — toàn bộ hoạt động là 1 người bán duy nhất.

### 1.4. Vision Statement

Trở thành trợ lý bán hàng AI đáng tin cậy cho hộ kinh doanh: giúp người bán không bỏ sót một khách hàng nào và chốt đơn nhanh hơn mà không cần tăng nhân sự.

---

## 2. Objectives & Success Metrics

### 2.1. SMART Goals (Phiên bản 1)

| ID | Goal |
|----|------|
| G-01 | Người bán có thể xem và trả lời tất cả tin nhắn từ Facebook và Zalo trong một giao diện thống nhất sau khi kết nối tài khoản. |
| G-02 | AI tự động xử lý ít nhất các tình huống FAQ (hỏi giá, hỏi sản phẩm, hỏi giao hàng) theo kịch bản được cấu hình mà không cần can thiệp. |
| G-03 | Mỗi cuộc hội thoại được AI phân loại ý định (hỏi thông tin / có nhu cầu mua / đã sẵn sàng chốt đơn) để người bán biết cần ưu tiên hội thoại nào. |
| G-04 | Đơn hàng được tạo từ hội thoại, người bán có thể xem trạng thái và cập nhật từ giao diện quản lý. |

### 2.2. KPIs & Success Signals

| KPI | Tín hiệu thành công |
|-----|-------------------|
| Không bỏ sót tin nhắn | 100% tin nhắn từ Facebook & Zalo xuất hiện trong hệ thống trong vòng 60 giây sau khi nhận |
| AI xử lý được FAQ | Người bán không cần trả lời thủ công cho câu hỏi đã cấu hình |
| Trạng thái đơn hàng rõ ràng | Người bán tra cứu được trạng thái bất kỳ đơn hàng trong < 10 giây |
| Người bán hài lòng | Người bán xác nhận không cần chuyển đổi qua lại Facebook/Zalo để xử lý tin nhắn hàng ngày |

---

## 3. Scope Boundaries

### 3.1. In-Scope (Phiên bản 1)

- **Module 1 — Kết nối nền tảng:** Kết nối Facebook Page và Zalo (OA và cá nhân); nhận tin nhắn vào hệ thống.
- **Module 2 — Unified Inbox:** Hộp thư hợp nhất hiển thị tất cả hội thoại, lọc theo nền tảng/trạng thái.
- **Module 3 — Quản lý khách hàng:** Hồ sơ khách hàng được tự động tạo từ hội thoại; ghi chú thủ công.
- **Module 4 — Quản lý sản phẩm:** Danh mục sản phẩm (tên, mô tả, ảnh, biến thể với giá và tồn kho); AI dùng để tư vấn.
- **Module 5 — AI Chatbot:** Trả lời tự động theo kịch bản; tư vấn sản phẩm; hỗ trợ thu thập thông tin đơn hàng; gửi thông tin thanh toán.
- **Module 6 — Quản lý đơn hàng:** Tạo đơn từ hội thoại; theo dõi trạng thái; cập nhật thủ công; tự động quản lý tồn kho theo trạng thái đơn.
- **Module 7 — Dashboard:** Tổng quan hội thoại, đơn hàng, cảnh báo chưa xử lý.
- **Module 8 — Xác thực & Phân quyền:** Đăng nhập / đăng xuất cho người bán; bảo vệ dữ liệu.

### 3.2. Out-of-Scope / Exclusions

- Tích hợp nền tảng khác (TikTok Shop, Instagram, Shopee...).
- Hỗ trợ nhiều hộ kinh doanh / multi-tenant.
- Tích hợp đơn vị vận chuyển (GHN, GHTK...).
- Thanh toán online / cổng thanh toán.
- Tính năng marketing automation (broadcast, remarketing).
- App di động native (iOS/Android) — chỉ web.
- Password reset, SSO, chia sẻ tài khoản.
- MCP hoặc tính năng chưa được phê duyệt.

> [!IMPORTANT]
> Bất kỳ tính năng nào không nằm trong danh sách In-Scope đều bị loại khỏi phiên bản 1, kể cả khi có yêu cầu phát sinh trong quá trình phát triển.

---

## 4. Functional Requirements & User Stories

### Module 1 — Kết nối nền tảng

**FR-01:** Hệ thống cho phép người bán kết nối Facebook Page thông qua luồng OAuth của Facebook.

**FR-02:** Hệ thống cho phép người bán kết nối Zalo OA thông qua luồng xác thực của Zalo. Hệ thống cũng hỗ trợ kết nối Zalo cá nhân (trong phạm vi API cho phép).

**FR-03:** Hệ thống hiển thị trạng thái kết nối (đã kết nối / ngắt kết nối / lỗi) cho từng tài khoản nền tảng.

> **US-01:** Là người bán, tôi muốn kết nối Facebook Page của mình vào hệ thống để tin nhắn từ Facebook tự động xuất hiện trong hộp thư của tôi.
>
> **US-02:** Là người bán, tôi muốn biết tài khoản Facebook/Zalo của mình đang kết nối hay không để tôi xử lý khi có sự cố.

---

### Module 2 — Unified Inbox

**FR-04:** Hệ thống hiển thị tất cả hội thoại từ Facebook và Zalo trong một danh sách chung (Unified Inbox), sắp xếp theo thời gian tin nhắn mới nhất.

**FR-05:** Hệ thống hiển thị badge nhận biết nền tảng (Facebook / Zalo) trên mỗi hội thoại.

**FR-06:** Hệ thống cho phép lọc hội thoại theo: nền tảng, trạng thái xử lý (mới / đang xử lý / đã xử lý).

**FR-07:** Người bán có thể xem toàn bộ lịch sử tin nhắn trong một hội thoại và trả lời trực tiếp từ giao diện. Nếu tin nhắn không gửi được (lỗi API / mất kết nối), hệ thống hiển thị thông báo lỗi rõ ràng. Tin nhắn không được đánh dấu là đã gửi và người bán có thể thử gửi lại.

**FR-08:** Hệ thống đánh dấu hội thoại là "đã đọc" khi người bán mở xem.

**FR-09:** Hệ thống hiển thị chỉ báo trạng thái AI (AI đang xử lý / AI đã chuyển cho người bán) trên mỗi hội thoại.

> **US-03:** Là người bán, tôi muốn thấy tất cả tin nhắn từ Facebook và Zalo trong một màn hình duy nhất để tôi không phải chuyển qua lại giữa các ứng dụng.
>
> **US-04:** Là người bán, tôi muốn lọc hội thoại theo nền tảng hoặc trạng thái để tập trung vào những hội thoại cần xử lý.
>
> **US-05:** Là người bán, tôi muốn trả lời tin nhắn trực tiếp từ hệ thống mà không cần vào Facebook hoặc Zalo.

---

### Module 3 — Quản lý khách hàng

**FR-10:** Hệ thống tự động tạo hồ sơ khách hàng khi có hội thoại đến từ một người dùng lần đầu (dựa trên ID người dùng của nền tảng).

**FR-11:** Hồ sơ khách hàng bao gồm: tên (lấy từ nền tảng), nền tảng, lịch sử hội thoại liên quan, lịch sử đơn hàng.

**FR-12:** Người bán có thể thêm ghi chú thủ công vào hồ sơ khách hàng.

**FR-13:** Hệ thống liên kết tự động các hội thoại của cùng một khách hàng từ cùng nền tảng (dựa trên ID nền tảng).

> **US-06:** Là người bán, tôi muốn xem thông tin và lịch sử mua hàng của một khách hàng ngay từ màn hình hội thoại để tôi tư vấn phù hợp hơn.

> [!NOTE]
> Một khách hàng được nhận dạng qua ID nền tảng (Facebook UID / Zalo UID). Việc ghép cùng một người dùng từ hai nền tảng khác nhau là **Out-of-Scope phiên bản 1**.

---

### Module 4 — Quản lý sản phẩm

**FR-14:** Người bán có thể tạo, sửa, xóa sản phẩm với các trường: tên, mô tả, ảnh, trạng thái (đang bán / ngừng bán).

**FR-14b:** Mỗi sản phẩm có thể có một hoặc nhiều **biến thể** (ví dụ: Size S/M/L, Màu Đỏ/Xanh). Mỗi biến thể có: tên biến thể, giá, và số lượng tồn kho riêng biệt.

**FR-14c:** Người bán có thể thêm, sửa, xóa từng biến thể trong một sản phẩm.

**FR-15:** Hệ thống hiển thị danh sách sản phẩm dạng bảng với tìm kiếm và lọc theo trạng thái.

**FR-15b:** Hệ thống hiển thị tổng tồn kho của sản phẩm (tổng của tất cả biến thể) trong danh sách. Người bán có thể cập nhật số lượng tồn kho của từng biến thể.

**FR-15c:** Hệ thống cảnh báo khi tồn kho của một biến thể xuống dưới ngưỡng tối thiểu (do người bán cấu hình, mặc định: 0).

**FR-16:** AI chatbot sử dụng danh mục sản phẩm (bao gồm biến thể và tồn kho) để tư vấn và trả lời câu hỏi về sản phẩm.

**FR-16b:** Khi AI hỗ trợ chốt đơn, AI hỏi khách hàng chọn biến thể cụ thể và chỉ chấp nhận biến thể có tồn kho > 0.

> **US-07:** Là người bán, tôi muốn quản lý danh sách sản phẩm của mình (thêm, sửa, xóa, quản lý biến thể) để AI có thể tư vấn đúng thông tin.
>
> **US-07b:** Là người bán, tôi muốn theo dõi tồn kho từng biến thể sản phẩm để biết khi nào cần nhập thêm hàng.
>
> **US-07c:** Là người bán, tôi muốn được cảnh báo khi tồn kho sắp hết để chủ động ngừng nhận đơn hoặc nhập thêm.

---

### Module 5 — AI Chatbot

**FR-17:** AI tự động trả lời tin nhắn đến trong vòng 30 giây dựa trên kịch bản được cấu hình và danh mục sản phẩm. Nếu AI service gặp lỗi kỹ thuật hoặc không phản hồi kịp thời, hội thoại tự động được gắn cờ "Cần người bán" và không có tin nhắn nào được gửi đến khách.

**FR-18:** Người bán có thể cấu hình kịch bản AI: câu hỏi thường gặp (FAQ) với câu trả lời tương ứng.

**FR-19:** AI phát hiện ý định mua hàng và bắt đầu thu thập thông tin đặt hàng theo thứ tự: sản phẩm → biến thể (nếu có) → số lượng → tên khách → số điện thoại → địa chỉ giao hàng.

**FR-20:** Khi AI không hiểu hoặc gặp tình huống ngoài kịch bản, AI gắn cờ hội thoại cần người bán xử lý và dừng tự động trả lời.

**FR-20b:** Khi khách hàng không phản hồi AI trong quá trình thu thập thông tin đặt hàng, hệ thống áp dụng timeout (thời gian do người bán cấu hình, mặc định: 24 giờ). Sau khi timeout, hội thoại chuyển về trạng thái "chưa xử lý", đơn hàng không được tạo, và AI sẵn sàng xử lý lại nếu khách quay lại.

**FR-21:** Người bán có thể tắt AI cho một hội thoại cụ thể để trả lời thủ công hoàn toàn.

**FR-22:** Người bán có thể bật lại AI cho hội thoại sau khi đã tắt.

**FR-22b:** Người bán có thể cấu hình template thông tin thanh toán (số tài khoản, tên ngân hàng, tên chủ tài khoản). AI sử dụng template này để gửi thông tin thanh toán cho khách hàng sau khi thu thập đủ thông tin đơn hàng, kèm tổng số tiền cần thanh toán. AI chỉ gửi đúng thông tin đã cấu hình, không bịa thêm.

**FR-22c:** Khi khách hàng yêu cầu thay đổi thông tin đơn hàng (địa chỉ, sản phẩm, số lượng...) sau khi đơn đã được tạo với trạng thái "Chờ xác nhận", AI tự động cập nhật thông tin trên đơn hàng và xác nhận lại toàn bộ đơn hàng đã cập nhật với khách. Nếu thay đổi liên quan đến sản phẩm hoặc biến thể, AI kiểm tra tồn kho trước khi cập nhật.

> **US-08:** Là người bán, tôi muốn AI tự động trả lời các câu hỏi thường gặp để tôi không phải lặp lại nhiều lần.
>
> **US-09:** Là người bán, tôi muốn AI báo cho tôi khi có khách muốn mua nhưng AI không xử lý được để tôi vào xử lý kịp.
>
> **US-10:** Là người bán, tôi muốn có thể tắt AI trong một hội thoại để trả lời trực tiếp khi tôi thấy cần.
>
> **US-10b:** Là người bán, tôi muốn AI tự động gửi thông tin thanh toán cho khách sau khi chốt đơn để tôi không cần copy-paste thủ công.
>
> **US-10c:** Là người bán, tôi muốn AI tự động cập nhật đơn khi khách thay đổi yêu cầu, để tôi không phải can thiệp vào mọi thay đổi nhỏ.

> [!NOTE]
> **Quyết định đã phê duyệt:**
> - AI **không tự xác nhận đơn hàng** — luôn cần người bán review và bấm xác nhận (OQ-03 ✅).
> - AI **có gửi thông tin thanh toán** theo template cấu hình sẵn (OQ-04 ✅).
> - AI **tự cập nhật** thông tin đơn khi khách thay đổi (OQ-07 ✅).
> - Hội thoại **timeout** khi khách không phản hồi (OQ-08 ✅).

---

### Module 6 — Quản lý đơn hàng

**FR-23:** Khi AI thu thập đủ thông tin đặt hàng, hệ thống tự động tạo đơn hàng với trạng thái "Chờ xác nhận".

**FR-24:** Người bán có thể xem danh sách đơn hàng với các trạng thái: Chờ xác nhận / Đã xác nhận / Đang giao / Hoàn thành / Đã hủy.

**FR-25:** Người bán có thể xác nhận, hủy hoặc cập nhật trạng thái đơn hàng thủ công.

**FR-25b:** Khi người bán xác nhận đơn hàng (chuyển sang "Đã xác nhận"), hệ thống tự động trừ tồn kho của các biến thể tương ứng theo số lượng trong đơn. Khi người bán hủy đơn hàng đã xác nhận (chuyển sang "Đã hủy"), hệ thống tự động cộng lại tồn kho.

**FR-26:** Người bán có thể tạo đơn hàng thủ công từ hội thoại (khi AI không tự tạo được).

**FR-27:** Đơn hàng liên kết hai chiều với hội thoại và hồ sơ khách hàng tương ứng: từ hội thoại có thể xem đơn hàng liên quan và ngược lại.

**FR-28:** Mỗi đơn hàng lưu: sản phẩm, biến thể đã chọn, số lượng, giá tại thời điểm đặt, thông tin giao hàng (tên, SĐT, địa chỉ), ghi chú, trạng thái, thời gian tạo.

> **US-11:** Là người bán, tôi muốn thấy danh sách đơn hàng và trạng thái của chúng để tôi biết cần xử lý gì tiếp theo.
>
> **US-12:** Là người bán, tôi muốn xác nhận hoặc hủy đơn hàng từ giao diện quản lý.
>
> **US-13:** Là người bán, tôi muốn tạo đơn hàng thủ công khi tôi trực tiếp chốt đơn với khách.

> [!NOTE]
> **Thông tin đơn hàng bắt buộc:** tên khách, số điện thoại, địa chỉ giao hàng, ít nhất 1 sản phẩm với biến thể cụ thể (OQ-05 ✅).

---

### Module 7 — Dashboard

**FR-29:** Dashboard hiển thị tổng quan: số hội thoại mới, số hội thoại chưa xử lý, số đơn hàng đang chờ xác nhận.

**FR-30:** Hệ thống cảnh báo (badge / notification) khi có hội thoại mới hoặc hội thoại cần người bán xử lý.

> **US-14:** Là người bán, tôi muốn xem tổng quan hoạt động ngay khi vào hệ thống để biết cần làm gì ngay.

---

### Module 8 — Xác thực & Phân quyền

**FR-31:** Người bán đăng nhập bằng email và mật khẩu.

**FR-32:** Hệ thống hỗ trợ đăng xuất. Session bị hủy hoàn toàn sau khi đăng xuất.

**FR-33:** Chỉ người dùng đã đăng nhập mới có thể truy cập dữ liệu của hệ thống.

**FR-34:** Toàn bộ dữ liệu (hội thoại, khách hàng, sản phẩm, đơn hàng) thuộc về một hộ kinh doanh duy nhất — không có chia sẻ hay truy cập chéo.

> **US-15:** Là người bán, tôi muốn đăng nhập bằng email/mật khẩu để bảo vệ dữ liệu kinh doanh của mình.

---

## 5. Observable Acceptance Criteria

### Module 1 — Kết nối nền tảng

**AC-01 (FR-01):** Khi người bán hoàn tất luồng OAuth Facebook, trang Cài đặt hiển thị tên Facebook Page và trạng thái "Đã kết nối". Tin nhắn mới gửi đến Page xuất hiện trong Inbox trong vòng 60 giây.

**AC-02 (FR-02):** Khi người bán hoàn tất xác thực Zalo (OA hoặc cá nhân), trang Cài đặt hiển thị tên tài khoản Zalo, loại tài khoản (OA / cá nhân), và trạng thái "Đã kết nối". Tin nhắn mới từ Zalo xuất hiện trong Inbox trong vòng 60 giây.

**AC-03 (FR-03):** Khi token kết nối hết hạn hoặc bị thu hồi, hệ thống hiển thị trạng thái "Lỗi kết nối" và hướng dẫn kết nối lại. Không có tin nhắn giả mạo được tạo ra.

---

### Module 2 — Unified Inbox

**AC-04 (FR-04):** Mở Unified Inbox, người bán thấy tất cả hội thoại từ Facebook và Zalo trong một danh sách, sắp xếp theo tin nhắn mới nhất lên trên.

**AC-05 (FR-05):** Mỗi dòng hội thoại hiển thị icon/badge phân biệt rõ ràng Facebook hoặc Zalo.

**AC-06 (FR-06):** Chọn bộ lọc "Facebook" → chỉ hiển thị hội thoại từ Facebook. Chọn "Zalo" → chỉ Zalo. Chọn "Chưa xử lý" → chỉ hội thoại chưa có người bán xử lý.

**AC-07 (FR-07):** Mở một hội thoại, người bán thấy toàn bộ lịch sử tin nhắn theo thứ tự thời gian. Nhập tin nhắn và nhấn Gửi → tin nhắn xuất hiện trong hội thoại và được gửi đến khách hàng qua nền tảng tương ứng. Nếu tin nhắn không gửi được (lỗi API / mất kết nối), hệ thống hiển thị thông báo lỗi rõ ràng trong giao diện hội thoại. Tin nhắn không được đánh dấu là đã gửi. Người bán có thể thử gửi lại.

**AC-08 (FR-08):** Hội thoại có tin nhắn chưa đọc hiển thị chỉ báo bold/badge. Sau khi người bán mở hội thoại, chỉ báo chưa đọc biến mất.

**AC-09 (FR-09):** Mỗi hội thoại hiển thị trạng thái AI: "AI đang xử lý" hoặc "Cần người bán" hoặc "Người bán đang xử lý".

---

### Module 3 — Quản lý khách hàng

**AC-10 (FR-10):** Khi một người dùng Facebook/Zalo nhắn tin lần đầu tiên, hệ thống tự động tạo hồ sơ khách hàng. Không cần người bán thao tác.

**AC-11 (FR-11):** Mở hồ sơ khách hàng: hiển thị tên, nền tảng, danh sách hội thoại, danh sách đơn hàng liên quan.

**AC-12 (FR-12):** Người bán nhập ghi chú vào hồ sơ khách hàng và nhấn Lưu → ghi chú xuất hiện trong hồ sơ ngay sau đó và vẫn còn sau khi F5.

**AC-12b (FR-13):** Cùng một Facebook UID nhắn tin trong 2 hội thoại khác nhau → cả 2 hội thoại xuất hiện trong hồ sơ khách hàng đó. Không tạo ra 2 hồ sơ khách hàng trùng lặp.

---

### Module 4 — Quản lý sản phẩm

**AC-13 (FR-14):** Người bán tạo sản phẩm mới với tên, mô tả, ảnh → sản phẩm xuất hiện trong danh sách. Người bán sửa tên sản phẩm → tên mới được lưu. Người bán xóa sản phẩm → sản phẩm không còn trong danh sách.

**AC-13b (FR-14b):** Người bán thêm biến thể "Size M - Màu Đỏ" với giá 150.000đ và tồn kho 10 → biến thể xuất hiện trong sản phẩm. Người bán sửa giá biến thể → giá mới được lưu. Người bán xóa biến thể → biến thể không còn trong sản phẩm.

**AC-13c (FR-14c):** Sản phẩm có ít nhất 1 biến thể hợp lệ thì mới được lưu / đặt trạng thái đang bán. Nếu xóa hết biến thể thì sản phẩm tự động chuyển trạng thái ngừng bán.

**AC-14 (FR-15):** Nhập từ khóa vào ô tìm kiếm → danh sách lọc theo tên sản phẩm khớp với từ khóa. Chọn lọc "Đang bán" → chỉ hiển thị sản phẩm đang bán.

**AC-14b (FR-15b):** Danh sách sản phẩm hiển thị cột "Tồn kho" với tổng số lượng của tất cả biến thể. Người bán sửa số lượng tồn kho của biến thể → giá trị mới được lưu và tổng tồn kho cập nhật ngay.

**AC-14c (FR-15c):** Khi tồn kho của một biến thể bằng 0 (hoặc xuống dưới ngưỡng cấu hình), hệ thống hiển thị cảnh báo màu đỏ / badge "Hết hàng" trên sản phẩm đó trong danh sách.

**AC-15 (FR-16):** Khi khách hàng hỏi về một sản phẩm đang bán, AI trả lời với thông tin chính xác từ danh mục (tên, giá, mô tả, các biến thể hiện có). AI không bịa thêm thông tin sản phẩm ngoài danh mục.

**AC-15b (FR-16b):** Khi AI hỗ trợ đặt hàng, AI hỏi khách chọn biến thể. Nếu khách chọn biến thể hết hàng (tồn kho = 0), AI thông báo hết hàng và đề xuất biến thể còn hàng khác. AI không tạo đơn hàng với biến thể hết hàng.

---

### Module 5 — AI Chatbot

**AC-16 (FR-17):** Gửi tin nhắn từ tài khoản test → trong vòng 30 giây, AI trả lời tự động. Nếu không có kịch bản phù hợp, AI gắn cờ hội thoại cần người bán. Nếu AI service không phản hồi trong vòng 30 giây do lỗi kỹ thuật, hội thoại tự động được gắn cờ "Cần người bán" và không có tin nhắn nào được gửi đến khách. Người bán nhìn thấy cảnh báo trong Inbox.

**AC-17 (FR-18):** Người bán tạo FAQ "Giá sản phẩm X là bao nhiêu?" → "Sản phẩm X giá Y đồng". Khi khách hỏi câu tương tự, AI trả lời theo FAQ.

**AC-18 (FR-19):** Khi khách hàng bày tỏ ý định mua, AI hỏi lần lượt: sản phẩm → biến thể → số lượng → tên → SĐT → địa chỉ. Sau khi thu thập đủ, AI thông báo đơn hàng đã được ghi nhận và hiển thị tóm tắt.

**AC-19 (FR-20):** Khi AI nhận tin nhắn không thuộc kịch bản và không thể xử lý, hội thoại bị gắn cờ "Cần người bán" trong Inbox. AI không tiếp tục trả lời hội thoại đó cho đến khi người bán tắt AI hoặc xử lý xong.

**AC-19b (FR-20b):** Khi khách không phản hồi trong khoảng thời gian cấu hình (mặc định 24 giờ) trong lúc AI đang thu thập thông tin đặt hàng → hội thoại chuyển về trạng thái "chưa xử lý". Đơn hàng không được tạo. Khi khách quay lại nhắn tin → AI bắt đầu lại từ đầu.

**AC-20 (FR-21):** Người bán nhấn nút "Tắt AI" trong hội thoại → AI ngừng tự động trả lời hội thoại đó. Tin nhắn tiếp theo của khách không được AI trả lời tự động.

**AC-21 (FR-22):** Người bán nhấn "Bật lại AI" → AI tiếp tục tự động trả lời hội thoại đó từ tin nhắn tiếp theo.

**AC-21b (FR-22b):** Người bán cấu hình template thanh toán (số TK, tên NH, tên chủ TK) → Khi AI thu thập đủ thông tin đơn hàng, AI tự động gửi tin nhắn cho khách hàng chứa tóm tắt đơn hàng kèm thông tin thanh toán và tổng tiền. Nếu chưa cấu hình template → AI không gửi thông tin thanh toán, chỉ tóm tắt đơn hàng.

**AC-21c (FR-22c):** Sau khi đơn hàng được tạo ("Chờ xác nhận"), khách nhắn "đổi địa chỉ thành ABC" → AI cập nhật địa chỉ trên đơn hàng, gửi lại tóm tắt đơn hàng đã cập nhật cho khách. Thay đổi được lưu và hiển thị trong chi tiết đơn hàng phía người bán. Nếu khách muốn đổi sản phẩm/biến thể mà biến thể mới hết hàng → AI thông báo hết hàng, đơn không được cập nhật.

---

### Module 6 — Quản lý đơn hàng

**AC-22 (FR-23):** Khi AI thu thập đủ thông tin đặt hàng bắt buộc, một đơn hàng mới xuất hiện trong danh sách đơn hàng với trạng thái "Chờ xác nhận". Đơn hàng liên kết đúng với hội thoại và khách hàng.

**AC-22b (FR-27):** Mở hội thoại đã có đơn hàng → danh sách đơn hàng liên quan hiển thị trong panel bên. Nhấn vào tên đơn → chuyển đến trang chi tiết đơn hàng. Mở chi tiết đơn hàng → có link về hội thoại gốc.

**AC-23 (FR-24):** Mở danh sách đơn hàng, người bán thấy tất cả đơn hàng với trạng thái rõ ràng. Lọc theo trạng thái "Chờ xác nhận" → chỉ hiển thị đơn hàng cần xác nhận.

**AC-24 (FR-25):** Người bán nhấn "Xác nhận" → trạng thái đơn hàng chuyển sang "Đã xác nhận". Người bán nhấn "Hủy" → trạng thái chuyển sang "Đã hủy". Thay đổi được lưu và hiển thị ngay.

**AC-24b (FR-25b):** Người bán xác nhận đơn hàng chứa "Áo size M x2" (tồn kho trước đó = 10) → tồn kho biến thể "size M" giảm xuống 8. Người bán hủy đơn hàng đã xác nhận → tồn kho tăng lại thành 10. Nếu xác nhận đơn mà tồn kho không đủ → hiển thị cảnh báo, không cho xác nhận.

**AC-25 (FR-26):** Người bán mở một hội thoại và nhấn "Tạo đơn hàng thủ công" → form nhập thông tin đơn hàng xuất hiện. Điền đủ thông tin và lưu → đơn hàng mới được tạo và liên kết với hội thoại.

**AC-26 (FR-28):** Mở chi tiết đơn hàng, người bán thấy: danh sách sản phẩm + biến thể đã chọn + số lượng + giá, thông tin giao hàng, ghi chú, trạng thái, thời gian tạo.

---

### Module 7 — Dashboard

**AC-27 (FR-29):** Mở Dashboard: hiển thị số liệu tổng quan cập nhật (hội thoại mới hôm nay, hội thoại chưa xử lý, đơn hàng chờ xác nhận). Số liệu thay đổi khi có sự kiện mới mà không cần F5.

**AC-28 (FR-30):** Khi có tin nhắn mới đến, badge thông báo xuất hiện trên Inbox trong nav mà không cần tải lại trang.

---

### Module 8 — Xác thực

**AC-29 (FR-31):** Nhập email/mật khẩu đúng → đăng nhập thành công, chuyển đến Dashboard. Nhập sai → hiển thị thông báo lỗi chung ("Email hoặc mật khẩu không đúng"), không cho vào hệ thống. Không tiết lộ email có tồn tại hay không.

**AC-30 (FR-33):** Truy cập URL bất kỳ trong hệ thống khi chưa đăng nhập → bị chuyển về trang đăng nhập.

**AC-31 (FR-34):** Không có API endpoint nào trả về dữ liệu của hộ kinh doanh khi request không có token hợp lệ.

**AC-32 (FR-32):** Người bán nhấn "Đăng xuất" → session bị hủy, người bán bị chuyển về trang đăng nhập. Nếu người bán cố truy cập URL nội bộ sau đó → bị chuyển về trang đăng nhập (không truy cập được dữ liệu).

---

## 6. Technical Considerations & Non-Functional Requirements

> [!NOTE]
> Phần này mô tả **kỳ vọng về hành vi sản phẩm**, không phải quyết định kỹ thuật cụ thể.

### 6.1. Performance

- Tin nhắn mới từ nền tảng xuất hiện trong Inbox trong vòng 60 giây.
- AI phản hồi khách hàng trong vòng 30 giây từ khi nhận tin nhắn.
- Giao diện web tải trang chính trong vòng 3 giây trên kết nối băng thông rộng bình thường.

### 6.2. Authentication & Authorization

- Người bán phải đăng nhập để truy cập bất kỳ chức năng nào.
- Session phải hết hạn sau khoảng thời gian không hoạt động (giả định: 24 giờ).
- Token kết nối Facebook/Zalo được lưu trữ an toàn, không lộ ra phía client.
- Thông báo lỗi đăng nhập không tiết lộ thông tin nhạy cảm.

### 6.3. Data Isolation & Security

- Toàn bộ dữ liệu (hội thoại, khách hàng, sản phẩm, đơn hàng) gắn với một hộ kinh doanh duy nhất.
- Dữ liệu khách hàng (tên, SĐT, địa chỉ) phải được lưu trữ bảo mật.
- Lịch sử hội thoại không bị xóa khi đơn hàng kết thúc (phục vụ tra cứu lịch sử).
- Thông tin thanh toán (template ngân hàng) được lưu an toàn, chỉ gửi qua kênh nền tảng đã kết nối.

### 6.4. Availability

- Hệ thống phải khả dụng ít nhất trong giờ kinh doanh (7:00–22:00).
- Khi mất kết nối với Facebook/Zalo API, hệ thống hiển thị cảnh báo rõ ràng và không mất dữ liệu đã nhận.

---

## 7. Assumptions

| ID | Giả định |
|----|---------|
| A-01 | Mỗi khách hàng được nhận dạng qua ID nền tảng (Facebook UID / Zalo UID). Không ghép cùng người dùng từ hai nền tảng. |
| A-02 | Sản phẩm có biến thể (size, màu...) — đã phê duyệt (OQ-01 ✅). |
| A-03 | Tồn kho được quản lý theo từng biến thể — đã phê duyệt (OQ-02 ✅). |
| A-04 | AI không tự xác nhận đơn hàng — luôn cần người bán review và bấm xác nhận. |
| A-05 | Thông tin bắt buộc của đơn hàng: tên khách, số điện thoại, địa chỉ, ít nhất 1 sản phẩm với biến thể cụ thể. |
| A-06 | Hệ thống là web app — không có app di động trong phiên bản 1. |
| A-07 | Chỉ có 1 người dùng (người bán) — không có phân quyền nhân viên. |
| A-08 | Zalo hỗ trợ cả OA (Official Account) và cá nhân — đã phê duyệt (OQ-06 ✅). |

---

## 8. Decisions Log

| ID | Câu hỏi | Quyết định | Ngày |
|----|--------|-----------|------|
| OQ-01 | Sản phẩm có biến thể không? | ✅ Có biến thể | 2026-09-08 |
| OQ-02 | Có quản lý tồn kho không? | ✅ Có tồn kho theo biến thể | 2026-09-08 |
| OQ-03 | AI có tự xác nhận đơn hàng không? | ✅ Không — cần người bán xác nhận | 2026-09-08 |
| OQ-04 | AI có gửi thông tin thanh toán không? | ✅ Có — theo template cấu hình | 2026-09-08 |
| OQ-05 | Thông tin đơn hàng bắt buộc? | ✅ Tên, SĐT, địa chỉ, sản phẩm + biến thể | 2026-09-08 |
| OQ-06 | Zalo OA hay cá nhân? | ✅ Cả hai | 2026-09-08 |
| OQ-07 | Khách thay đổi đơn sau khi tạo? | ✅ AI tự cập nhật và xác nhận lại | 2026-09-08 |
| OQ-08 | Khách không phản hồi? | ✅ Timeout → chuyển về chưa xử lý | 2026-09-08 |

---

## Validation Checklist

- [x] Mỗi FR phục vụ mục tiêu cốt lõi của sản phẩm.
- [x] Acceptance criteria có thể quan sát và kiểm tra được.
- [x] Xác thực, lưu trữ và phân quyền được làm rõ.
- [x] Exclusions ngăn feature expansion.
- [x] Không có requirement nào phụ thuộc MCP.
- [x] Không có tính năng nào được trình bày là đã hoàn thành.
- [x] Main journey và failure journey đều có thể test.
- [x] Thuật ngữ nhất quán (thời gian đồng nhất 60s nhận / 30s AI phản hồi).
- [x] Tất cả Open Questions đã được giải quyết.

---

*PRD v1.0 — Approved. Đã phê duyệt bởi người bán.*
