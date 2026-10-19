---
name: socialcart-frontend-patterns
description: Implement UI React/TypeScript/MUI, API state và realtime của SocialCart theo interaction contract đã chọn.
---

# SocialCart Frontend Patterns

Đọc [design brief](../../../docs/product-design-brief.md), [design decision](../../../docs/product-design.md), [data rules](../../../docs/data-rules.md), [OpenAPI](../../../docs/api/openapi.yaml). Concept B: Outfit/fallback, nền sáng ấm, AI teal, handoff cam; không dùng theme ví dụ cũ.

React18 + TypeScript + MUI5, Query5 cho server state, Zustand stores cho UI/session memory. Cấu trúc src/services, stores, pages, components, hooks, socket, theme, types. VITE_API_URL gồm /api/v1; relative endpoint /conversations không lặp prefix. Access trong memory, refresh HttpOnly cookie; single-flight refresh một lần, không localStorage token.

Conversation status NEW/IN_PROGRESS/RESOLVED; ai_status AI_HANDLING/NEEDS_SELLER/SELLER_HANDLING; is_read boolean độc lập. Không dùng status map gộp unread/ai/closed. Socket event envelope ở service-contracts; refetch sau reconnect, dedupe ID/version, cleanup listener.

Inbox desktop list360/chat/info; mobile list→chat/back, info toggle. Quick order centered dialog, focus trap/return, Escape; loading/empty/error/send retry giữ input; disabled khi disconnect/hết hàng. Bật/tắt AI qua HTTP có expected_version. Giá hiển thị VND integer, thời gian UI Asia/Ho_Chi_Minh.

Không coi prototype mock auth/order là API thật. Test theo AC và checklist P4.5; ghi rõ checks chưa chạy.
