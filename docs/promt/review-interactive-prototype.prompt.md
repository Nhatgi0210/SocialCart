# P4.5 — Review interactive prototype SocialCart

Chạy [prototype](../../prototype/) theo [setup](../setup.md). Kiểm checklist ở [prototype-review](../prototype-review.md): login → inbox/filter → conversation → AI/handoff → seller reply/retry → quick order → empty/error. Kiểm viewport 320/375/768/1440, keyboard-only, focus trap/return, Escape, labels/live region, contrast và reduced motion.

Với mỗi issue ghi evidence/screenshot, bước tái hiện, expected/actual, ảnh hưởng và correction nhỏ nhất. Ghi PASS/FAIL/NOT RUN/BLOCKED; không suy kết quả runtime từ source. Không redesign scope hoặc giả lập backend persistence. Người dùng chấp nhận correction/rủi ro trước khi cập nhật docs/product-design.md thành accepted prototype.


Đọc [AGENTS](../../AGENTS.md), [decision log](../decisions.md), [design brief](../product-design-brief.md), [product design](../product-design.md). Các skill thiết kế ngoài repository chỉ dùng nếu thực sự có sẵn, không coi tên skill trong template cũ là dependency bắt buộc. Giữ phạm vi SocialCart; không thêm register, ticket board, Kanban hoặc backend vào prototype.
