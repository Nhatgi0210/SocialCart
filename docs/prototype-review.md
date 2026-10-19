# P4.5 — Kế hoạch và trạng thái review prototype

Ngày: 2026-10-19. **Chưa nghiệm thu prototype.** Lượt bổ sung tài liệu này đọc source và đối chiếu đặc tả, chưa chạy audit trình duyệt, screen reader hay mobile thật. Không tự chuyển design brief từ Draft sang Approved.

## Phạm vi và chuẩn đối chiếu

[Design brief](product-design-brief.md), [Concept B](product-design.md), `prototype/`. Luồng SocialCart: login → inbox/lọc → conversation → AI response/handoff → trả lời/retry → tạo đơn → empty/error. Không dùng checklist Kanban/ticket từ template cũ. Prototype không chứng minh JWT, DB, transaction tồn kho hoặc tích hợp nền tảng.

| Check | Cách kiểm tra / kết quả mong đợi | Trạng thái |
| --- | --- | --- |
| Login | Sai/thiếu input có lỗi; Enter không submit đôi; loading rõ | NOT RUN |
| Inbox | Sort, badge FB/Zalo, chưa đọc, filter và no-result đúng brief | NOT RUN |
| Chat | Phân biệt CUSTOMER/AI/SELLER; typing biến mất sau success/failure | NOT RUN |
| Handoff | Cảnh báo rõ; toggle AI và reply đúng trạng thái | NOT RUN |
| Tạo đơn | Modal giữa màn hình; required/stock; liên kết đơn-hội thoại | NOT RUN |
| Recovery | Text giữ lại khi gửi lỗi; retry rõ; disconnect disable input | NOT RUN |
| Keyboard | Tab order, focus ring, Enter/Space, Escape, focus trap/return | NOT RUN |
| Narrow | 320/375/768px; back chat, drawer và modal không mất control | NOT RUN |
| Reduced motion | Bật prefers-reduced-motion; thông tin giữ nguyên, dừng animation | NOT RUN |
| Accessibility | Labels, live region, contrast đo được và touch target | NOT RUN |

Mỗi issue ghi: ID, bước tái hiện, screenshot/viewport/browser, kỳ vọng so với quan sát, ảnh hưởng, correction nhỏ nhất, trạng thái xử lý. Người dùng review correction và rủi ro còn lại trước khi coi prototype là accepted reference. Đây là gate đã có trong quy trình P4.5, không phải phê duyệt mới cho công việc tài liệu.

Điểm lệch tài liệu đã xử lý: collection timeout phải reset về NEW và AI sẵn sàng theo PRD, không gộp với lỗi AI chuyển người bán. Landing sản phẩm cuối là Dashboard theo AC-29, còn prototype tập trung Inbox. Chưa kết luận prototype đã đúng hai điểm này cho đến khi kiểm tra runtime.
