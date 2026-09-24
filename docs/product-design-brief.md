# SocialCart product design brief

> **Provenance**
> - **Source prompt:** [P4.1 — Create product design brief](../../chapter-04-ai-for-product-design/prompts/create-product-design-brief.prompt.md)
> - **Artifact status:** `Draft — pending human approval`
> - **Human action:** Review interaction contracts and approve behavior before visual exploration.
> - **Reproduction note:** Visual references and human choices from HUMAN CHECK will influence concept exploration in P4.2.

## Status and boundary

**Scope prototype:** Unified Inbox + Chat with AI + Quick Order creation. This artifact is the product-design source of truth for session entry, conversation management, AI-assisted chat, AI→human handoff, and order creation from chat. The prototype remains disposable and does not call a backend; later work must preserve this behavior in architecture, implementation, tests, documentation, and release evidence.

## Problem

Người bán nhỏ kinh doanh qua Facebook và Zalo phải chuyển đổi qua lại giữa nhiều ứng dụng để trả lời tin nhắn khách hàng. Họ bỏ sót tin nhắn, phản hồi chậm, và không biết AI đang xử lý hội thoại nào hay cần can thiệp ở đâu. Giao diện cần giảm cognitive load — không phải một dashboard phức tạp, mà là một unified inbox nơi mọi hội thoại, trạng thái AI, và hành động chốt đơn xảy ra trong một luồng liên tục.

## Conversation list contract

| Field | Rule |
| --- | --- |
| Customer name | Required; pulled from platform profile. |
| Platform badge | Required; visual icon distinguishing Facebook or Zalo. |
| Last message preview | Required; truncated to single line; marks AI-generated messages distinctly. |
| Timestamp | Required; relative time (e.g. "5 phút trước"); absolute after 24h. |
| Unread indicator | Bold name + unread dot when conversation has unread messages. Cleared when seller opens conversation. |
| AI status label | Required; one of three states (see AI status contract below). |
| Processing status | One of: `Mới` / `Đang xử lý` / `Đã xử lý`. |

**Sort order:** Most recent message first, always.

**Filters:**
- Platform: Tất cả / Facebook / Zalo
- Status: Tất cả / Mới / Đang xử lý / Đã xử lý

## AI status contract

| Status | Meaning | Visual signal |
| --- | --- | --- |
| AI đang xử lý | AI is actively handling this conversation | Bot icon + green indicator |
| Cần người bán | AI flagged — seller intervention required | Bell icon + amber indicator |
| Người bán đang xử lý | Seller has taken over, AI is off | Person icon + neutral/grey indicator |

**State transitions:**

| From → To | Trigger |
| --- | --- |
| AI đang xử lý → Cần người bán | AI encounters unknown intent, AI service error, or customer timeout |
| AI đang xử lý → Người bán đang xử lý | Seller presses "Tắt AI" |
| Cần người bán → Người bán đang xử lý | Seller opens conversation and begins replying |
| Người bán đang xử lý → AI đang xử lý | Seller presses "Bật lại AI" |

**Controls:**
- "Tắt AI" button visible when status is `AI đang xử lý`. Immediate effect, no confirmation dialog.
- "Bật lại AI" button visible when status is `Người bán đang xử lý`. Immediate effect, no confirmation dialog.

## Chat view contract

### Message types

| Type | Visual distinction | Alignment |
| --- | --- | --- |
| Customer message | Platform-colored bubble or neutral customer bubble | Left |
| AI auto-response | Bot icon badge + "AI" label on bubble | Left (same side as customer context) or distinctly styled |
| Seller message | Different bubble color, no bot badge | Right |
| System event | Centered inline label (e.g. "AI đã chuyển cho người bán") | Center |

### Typing indicator
- When AI is composing a response, a typing indicator (animated dots or similar) appears in the chat, labeled with "AI đang trả lời…"
- Indicator disappears when the AI message arrives or when AI fails.

### Handoff signal
- When AI transfers to seller, a prominent system message appears: "🔔 AI đã chuyển hội thoại cho bạn"
- The AI status label in the conversation list updates immediately.
- Handoff must be **visually dramatic** — this is the most important action signal in the interface.

### Message input
- Always visible at bottom of chat view.
- Send button + Enter key to send.
- Empty input → send button disabled.
- When platform connection is in error state → input disabled + inline message: "Không thể gửi tin nhắn. Kết nối [Platform] đang bị gián đoạn."

### Send failure
- Failed message shows error icon + "Gửi thất bại" + "Thử lại" button.
- Message is NOT marked as sent. Seller can retry.

### Customer info sidebar
- Visible on desktop alongside chat view (3-panel layout).
- Shows: customer name, platform, conversation history links, order history links, manual notes.
- On narrow viewports: hidden by default, accessible via toggle button.

## Order creation contract

### Quick order modal (from chat)
- Triggered by "Tạo đơn hàng" button in chat view header or customer info sidebar.
- Opens as a **centered modal** — not a side panel.
- Pre-fills customer name from profile if available.

### Order fields

| Field | Rule |
| --- | --- |
| Customer name | Required; pre-filled from profile; max 100 chars. |
| Phone number | Required; 10–11 digits. |
| Delivery address | Required; max 500 chars. |
| Products | At least 1 product with specific variant. Selected from catalog. |
| Variant | Required if product has variants. |
| Quantity | Required; ≥ 1. |
| Notes | Optional. |

### Order behavior
- Created with status "Chờ xác nhận" — seller must confirm manually.
- Order links bidirectionally: chat → order detail, order detail → chat.
- Price captured at time of order creation (snapshot).

### Validation
- Missing required fields → inline error messages.
- Out-of-stock variant → disabled in selector + "Hết hàng" badge.
- Submit disabled until all required fields pass validation.

## Core journeys

1. **Login:** Enter email and password in a centered form. Resolve inline validation errors. Continue to inbox after success. Session-based, simulated auth for prototype.
2. **View inbox:** See all conversations sorted by recency. Scan platform badges, unread indicators, and AI status labels. Apply filters to focus.
3. **Open conversation:** Click conversation → chat view opens with full message history. Customer info sidebar visible on desktop. Unread indicator clears.
4. **Read AI response:** See AI auto-responses clearly distinguished from customer messages. See typing indicator while AI composes.
5. **Trigger handoff:** AI flags conversation → dramatic handoff signal appears → seller sees "Cần người bán" status. Or seller manually presses "Tắt AI".
6. **Reply as seller:** Type message in always-visible input. Send via button or Enter. See delivery status.
7. **Create order from chat:** Press "Tạo đơn hàng" → centered modal opens with pre-filled customer info → select products/variants → submit → order created as "Chờ xác nhận".
8. **Return AI control:** Seller presses "Bật lại AI" → AI resumes handling conversation.
9. **Recover from failure:** AI failure → no message sent to customer → conversation flagged → seller intervenes. Send failure → retry button. Both recovery paths are explicit.

## Information hierarchy

1. **Session entry:** Login form — email, password, one primary action.
2. **Inbox overview:** Conversation list with scan-critical info (unread, platform, AI status, last message).
3. **Active conversation:** Chat message history — message content dominates.
4. **AI signals:** Typing indicator, handoff notification, AI status badge.
5. **Customer context:** Sidebar info panel — name, platform, orders, notes.
6. **Order action:** Quick order modal — focused, centered, temporary.
7. **Recovery notices:** Error messages, retry buttons, connection warnings.

## States

### Loading
- Conversation list: skeleton placeholder rows (3–5 rows with shimmer animation).
- Chat history: centered spinner or skeleton message bubbles.
- Customer info: skeleton fields.

### Empty
- **Inbox empty (no connections):** Illustration + "Chưa có hội thoại. Hãy kết nối Facebook hoặc Zalo để bắt đầu." + clear action to settings.
- **Inbox empty (with connections, no messages yet):** "Chưa có hội thoại nào. Tin nhắn mới sẽ xuất hiện tại đây."
- **Filter returns no results:** "Không có hội thoại nào khớp bộ lọc."
- **No orders for customer:** "Chưa có đơn hàng."
- **Chat selected but empty:** Placeholder prompting selection or waiting for first message.

### Error and recovery
- **AI service failure:** Conversation auto-flagged "Cần người bán." No message sent to customer. Inbox shows warning badge. Seller sees alert in chat: "⚠️ AI gặp lỗi. Hội thoại cần bạn xử lý."
- **AI retry:** After AI failure, when seller re-enables AI ("Bật lại AI"), system attempts to reconnect AI. If still failing, re-flags immediately.
- **Send message failure:** Message stays in chat with error icon + "Gửi thất bại" + "Thử lại" button. Not marked as sent.
- **Platform disconnected:** Input area disabled. Inline warning with "Kết nối lại" action directing to settings.

### Disabled
- Send button disabled when input is empty.
- Message input disabled when platform connection is in error state.
- Order submit disabled when required fields are missing.
- Out-of-stock variants disabled in product selector.

### Focus and keyboard
- Tab navigates through conversation list items, chat input, action buttons.
- Enter sends message in chat input.
- Escape closes order modal.
- AI toggle buttons are focusable and operable via Enter/Space.
- Conversation list items selectable via Enter.
- Modal traps focus while open.

### Narrow viewport (< 768px)
- Conversation list takes full width. Selecting a conversation navigates to full-width chat view with back button.
- Customer info sidebar hidden; accessible via toggle icon in chat header.
- Order modal remains centered but full-width with scroll.
- All controls remain reachable.

### Reduced motion
- Typing indicator animation replaced with static "AI đang trả lời…" text.
- Skeleton shimmer replaced with static placeholder.
- Handoff notification still appears but without entrance animation.
- All states and actions preserved — only decorative motion removed.

## Accessibility and responsive behavior

- Login form submits with Enter, exposes field/form errors through live regions, disables duplicate submission, and retains visible labels.
- Conversation list items are semantic focusable controls with visible focus ring.
- Chat messages use appropriate ARIA roles for log/feed pattern.
- AI status changes announced via live region for screen readers.
- Handoff notification announced as alert.
- Order modal is a dialog with proper focus trap, Escape to close, and return focus to trigger element.
- Platform badges use accessible labels (not icon-only — include sr-only text "Facebook" or "Zalo").
- Color is never the sole indicator — all status signals combine icon + color + label.
- Touch targets minimum 44×44px on mobile.

## Explicit exclusions

No backend persistence, password reset, email verification, SSO, social login, multi-tenant/staff accounts, product management UI, product catalog editing, FAQ configuration, AI settings configuration, payment template setup, dashboard metrics, analytics, inventory management, shipping integration, platform connection setup (OAuth flows), TikTok/Instagram/Shopee, app di động, marketing automation, or order status lifecycle management beyond creation. Prototype auth is simulated and state resets on reload.

> [!NOTE]
> The prototype demonstrates the **conversation experience** only: inbox → chat → AI interaction → handoff → quick order creation. Configuration screens (products, FAQ, AI settings, platform connections) and order lifecycle management are out of prototype scope.

## Review gate

Later work must preserve the accepted conversation list contract, chat view contract (AI/human/customer message distinction), AI status state machine, handoff signal behavior, order creation modal pattern, empty/error/recovery states, and responsive accessibility behavior. Any product change requires an explicit decision record.
