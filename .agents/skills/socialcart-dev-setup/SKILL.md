---
name: socialcart-dev-setup
description: Chạy và debug môi trường local SocialCart, phân biệt prototype hiện có với application chưa scaffold.
---

# SocialCart Local Setup

Nguồn lệnh chính thức: [docs/setup.md](../../../docs/setup.md); biến mẫu: [.env.example](../../../.env.example). Đọc [trạng thái dự án](../../../docs/project-status.md) trước khi chạy lệnh: đã có scaffold BOOT-01/02, nhưng file tồn tại không chứng minh auth/migration/Compose đã chạy thành công.

Prototype từ root: `python -m http.server 5500 --bind 127.0.0.1 --directory prototype`.

Sau BOOT: Python 3.11 + dependencies pin, Node LTS tương thích lockfile; Compose MySQL/Redis; Alembic tập trung backend/shared/db; seed seller qua env. Không reset DB/xóa volume làm debug mặc định. Keys và .env không commit.

Auth RS256/access15m/refresh7d/idle24h; dùng đúng FB_WEBHOOK_VERIFY_TOKEN và VITE_API_URL đã gồm /api/v1. Cấu hình theo service; chưa bật adapter không bắt có credential Gemini/nền tảng. Worker chuẩn Linux/WSL2. ngrok :8000 cho callback qua Gateway.

Lệnh test/start mục tiêu và điều kiện áp dụng ở setup; không bịa script đã có hoặc báo test pass khi thiếu manifest. Báo kết quả local/simulated/live tách biệt.
