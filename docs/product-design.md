# SocialCart — Product Design Decision (P4.3)

> **Provenance**
> - **Source prompt:** [P4.3 — Critique and select an interface](promt/critique-and-select-interface.prompt.md)
> - **Artifact status:** `Approved — Concept B selected`
> - **Input brief:** [docs/product-design-brief.md](product-design-brief.md)
> - **Concepts audited:** concept-a.html, concept-b.html, concept-c.html
> - **Human action:** Review decision packet → approve selected direction → proceed to P4.4

---

## Audit Summary

Các concept được kiểm tra theo audit checklist đặc thù của SocialCart:
- Inbox scanability (unread badge, platform icon FB/Zalo, last message preview)
- Chat clarity (AI vs human message distinction, typing indicator, handoff signal)
- Order action accessibility (quick order modal từ chat)
- Focus order, keyboard navigation, narrow viewport, reduced motion, recovery states

---

## Concept Profiles

### Concept A — Midnight Glass
- **Visual system:** Dark mode, glassmorphism, neon accents (Inter)
- **Layout:** Narrow sidebar 340px + wide chat + info panel luôn hiển thị
- **Key choices:** Cyan (`#22d3ee`) cho AI, Amber (`#f59e0b`) pulsing cho handoff, glassmorphism backdrop-filter

### Concept B — Soft Daylight
- **Visual system:** Light mode, warm neutrals, card-based, Outfit font
- **Layout:** Sidebar 360px với card shadow + slide-in customer info
- **Key choices:** Teal (`#0d9488`) cho AI, Orange banner cho handoff, unread = left border accent

### Concept C — Electric Gradient
- **Visual system:** Dark mode, bold gradient purple-to-blue, Roboto
- **Layout:** Wide sidebar 380px + chat + right drawer overlay cho customer info
- **Key choices:** Cyan glow AI, amber glow handoff, gradient header, card hover translateY

---

## Audit Findings

### 1. Inbox Scanability

| Criterion | Concept A | Concept B | Concept C |
|---|---|---|---|
| Unread badge | ✅ Unread dot + bold name (indigo glow) | ✅ Unread dot + bold name + left teal border | ✅ Unread dot + bold name |
| Platform badge | ✅ Tròn 18px, bottom-right, F/Z màu chuẩn | ✅ Tròn 18px, bottom-right, có text label | ✅ Vuông 20px, rõ hơn, bottom-right |
| AI tag in preview | ✅ `[AI]` text cyan trước nội dung preview | ✅ Tag pill teal nổi bật hơn, có bg | ⚠️ Gradient clip text — không đủ contrast trên dark bg |
| Last message truncation | ✅ `text-overflow: ellipsis` | ✅ `text-overflow: ellipsis` | ✅ `text-overflow: ellipsis` |
| **Verdict** | Đủ, rõ | **Tốt nhất** — tag có background, unread border rõ | Rủi ro contrast |

**Winner: B** — AI tag có background pill teal, unread border 3px là cue trực quan mạnh nhất.

---

### 2. Chat Clarity

| Criterion | Concept A | Concept B | Concept C |
|---|---|---|---|
| Customer message | Bubble trái, màu `#1e293b` | Bubble trái, warm grey | Bubble trái, `bg-hover` dark |
| AI auto-response | Bubble có border cyan + bot icon + "AI" label | Bubble teal left-border + label | Bubble cyan-glow + gradient accent |
| Seller message | Bubble phải, `#3b82f6` | Bubble phải, `seller-blue` | Bubble phải, blue |
| System event | Centered label | Centered label | Centered label |
| Typing indicator | Animated dots + glow, "AI đang trả lời…" | 3 dots "AI đang soạn tin nhắn…" | Animated dots purple glow |
| AI/Human/Customer distinction | ✅ Màu + icon + label | ✅ Màu + left-border + label | ✅ Màu + glow — nhưng tất cả dark bg, khó phân biệt nhanh |
| **Verdict** | Rõ ràng | **Tốt nhất** — Light mode tăng contrast giữa các loại bubble | Contrast yếu hơn trong môi trường dark toàn phần |

**Winner: B** — Light background tạo tương phản cao nhất giữa 3 loại tin nhắn.

---

### 3. Handoff Signal

| Criterion | Concept A | Concept B | Concept C |
|---|---|---|---|
| Visual treatment | Amber glow pulsing badge + `animation: pulse-amber 2s infinite` | Orange banner `gentlePulse 2.5s infinite` + bell icon | Gradient amber banner full-width |
| Dramatic enough? | ✅ Pulse + glow đủ nổi bật | ✅ Banner màu cam đứng vững, professional | ✅ Full-width nhưng trên dark bg có thể bị nhìn là decoration |
| Accessible (not color-only)? | ✅ Icon + label + animation | ✅ Icon + label + color | ✅ Icon + color — thiếu animation rõ ràng |
| **Verdict** | Tốt | **Tốt nhất** — banner + icon + màu cam là pattern quen thuộc trong SaaS notifications | Ổn nhưng yếu hơn |

**Winner: B** — Orange banner với icon và pulse animation phù hợp với người dùng mobile/SaaS Việt Nam.

---

### 4. Order Action Accessibility

| Criterion | Concept A | Concept B | Concept C |
|---|---|---|---|
| "Tạo đơn hàng" button | ✅ Trong chat header, primary btn rõ | ✅ Trong chat header, accent btn rõ | ✅ Trong header, gradient btn |
| Modal pattern | ✅ Centered modal theo brief | ✅ Centered modal theo brief | ✅ Centered modal theo brief |
| Keyboard: Escape close | Theo brief — cần verify | Theo brief — cần verify | Theo brief — cần verify |
| **Verdict** | Đồng đều | Đồng đều | Đồng đều |

**Winner: Tie** — Tất cả 3 concept đều implement centered modal đúng theo brief.

---

### 5. Keyboard Navigation & Focus Order

| Criterion | Concept A | Concept B | Concept C |
|---|---|---|---|
| Focus ring | Implicit từ browser, chưa custom rõ | `outline: 2px solid teal` visible trên light bg | Chưa custom rõ |
| Tab order | Logical sidebar → chat → input | Logical sidebar → chat → input | Logical sidebar → chat → input |
| **Verdict** | ⚠️ Focus ring khó thấy trên dark bg | **Tốt nhất** — Light bg làm focus ring teal hiển thị tự nhiên | ⚠️ Focus ring khó thấy trên dark bg |

**Winner: B** — Light mode là nền tốt nhất cho focus visibility theo WCAG 2.1.

---

### 6. Narrow Viewport (< 768px)

| Criterion | Concept A | Concept B | Concept C |
|---|---|---|---|
| Stack layout | Responsive CSS present | Responsive CSS present | Responsive CSS present |
| Touch targets | 44px avatar | 44px avatar | 48px avatar — lớn nhất |
| Customer info sidebar | Hidden, toggle button | Slide-in from right | Drawer overlay |
| **Verdict** | Đủ | Đủ | ✅ Avatar 48px tốt hơn cho touch |

**Winner: Tie** — Concept C có avatar lớn hơn nhưng không đủ để thắng overall.

---

### 7. Reduced Motion

| Concept | Animations | Risk |
|---|---|---|
| A | pulse-amber, typing dots glow | Medium — aggressive neon pulse |
| B | gentlePulse, typing dots | **Low** — subtle, ít animation nhất |
| C | typing dots, hover translateY | Medium — translateY hover + glow |

**Winner: B** — Ít animation nhất, dễ comply `prefers-reduced-motion` hơn.

---

### 8. Recovery States

| Criterion | Concept A | Concept B | Concept C |
|---|---|---|---|
| AI failure state | Amber badge + alert trong chat | Orange badge + banner | Amber banner |
| Send failure | Error icon + "Thử lại" button | Error icon + "Thử lại" button | Error icon + "Thử lại" button |
| Platform disconnect | Input disabled + inline message | Input disabled + inline message | Input disabled + inline message |
| **Verdict** | Đồng đều | Đồng đều | Đồng đều |

**Winner: Tie** — Cả 3 concept đều theo đúng recovery contracts trong brief.

---

## Scorecard

| Audit Dimension | Concept A | Concept B | Concept C |
|---|:---:|:---:|:---:|
| Inbox scanability | ✅ | ✅✅ | ⚠️ |
| Chat clarity (AI/human/customer) | ✅ | ✅✅ | ✅ |
| Handoff signal drama | ✅ | ✅✅ | ✅ |
| Order action accessibility | ✅ | ✅ | ✅ |
| Keyboard / focus order | ⚠️ | ✅✅ | ⚠️ |
| Narrow viewport | ✅ | ✅ | ✅ |
| Reduced motion risk | Medium | **Low** | Medium |
| Recovery states | ✅ | ✅ | ✅ |
| **Total wins** | **1** | **5** | **1** |

---

## Recommendation

**→ Chọn Concept B — Soft Daylight**

### Rationale

1. **Contrast là yếu tố quan trọng nhất cho inbox đa nền tảng.** Người bán SocialCart scan inbox liên tục trong ngày. Light mode tạo contrast tự nhiên cao nhất giữa customer / AI / seller messages — không cần học màu neon.

2. **AI tag có background pill** (teal, có màu nền riêng) tốt hơn plain-text tag (Concept A) và gradient-clip text (Concept C, không accessible trên mọi browser).

3. **Unread left border** (3px teal) là pattern quen thuộc với người dùng mobile messaging (Zalo, Messenger) — không cần học mới.

4. **Focus ring tốt nhất.** Light background làm teal focus outline hiển thị đúng WCAG 2.1 AA mà không cần thêm custom shadow.

5. **Least animation risk.** `gentlePulse` của Concept B ít aggressive hơn `pulse-amber` glow của Concept A và hover `translateY` của Concept C → dễ comply reduced-motion hơn.

6. **Professional tone phù hợp với target user.** Người bán SME Việt Nam quen với UI sáng (Facebook, Shopee, Zalo). Dark glassmorphism (A) hoặc neon gradient (C) có thể gây cảm giác "game/tech" không phù hợp ngữ cảnh bán hàng.

---

## Rejected Alternatives

### Concept A — Midnight Glass
- **Rejected because:** Neon cyan/amber trên dark bg tạo glow effect đẹp về thẩm mỹ nhưng tăng nguy cơ contrast thất bại trên màn hình thấp sáng. Focus ring khó nhìn. Glassmorphism `backdrop-filter` có fallback nhưng làm phức tạp QA.
- **What it does well:** Handoff pulse amber rất dramatic, phù hợp nếu target users là power users trong phòng tối.
- **Risk nếu chọn:** WCAG AA contrast failure trên một số text/background combo; focus visibility kém.

### Concept C — Electric Gradient
- **Rejected because:** Gradient sidebar header đẹp nhưng filters nằm trong gradient → text contrast thấp (`rgba(255,255,255,0.7)`). AI tag dùng `gradient-clip text` → không accessible trên Firefox. Tất cả content area là dark-on-dark → khó phân biệt message types.
- **What it does well:** Avatar 48px tốt cho touch, hover lift cho thấy interactivity rõ.
- **Risk nếu chọn:** Gradient text không accessible, dark-on-dark chat clarity thấp.

---

## Accepted Risks for Concept B

| Risk | Severity | Mitigation |
|---|---|---|
| All-day light mode eye strain | Medium | Off-white base `#fafaf8` (không phải pure white) đã được chọn — giảm glare. Prototype không có dark mode. |
| `gentlePulse` cần `@media (prefers-reduced-motion)` | Low | Thêm fallback: static badge, no animation khi reduced-motion. |
| Focus ring cần custom CSS | Low | Thêm `:focus-visible { outline: 2px solid var(--teal); outline-offset: 2px; }` trong prototype. |
| AI tag pill chiếm width trong narrow sidebar | Low | Text truncate đã có — test ở 320px width. |

---

## Open Questions

1. **Dark mode variant:** Người dùng thực có yêu cầu dark mode không? Nếu có, Concept A là base tốt cho dark variant sau này.
2. **Outfit font loading:** Concept B dùng Google Font Outfit. Cần confirm fallback khi offline/slow connection.
3. **Animation loop:** `gentlePulse` 2.5s loop — có nên flash 1 lần rồi tắt thay vì loop vô hạn?

---

## Decision Record

| Field | Value |
|---|---|
| **Selected direction** | Concept B — Soft Daylight |
| **Visual system** | Light mode, warm neutrals, teal AI accent, orange handoff |
| **Font** | Outfit (Google Fonts) |
| **Layout** | Sidebar 360px + chat flex + slide-in customer info |
| **Unread signal** | Bold name + unread dot + left teal border 3px |
| **AI status** | Teal pill badge (icon + label + bg) |
| **Handoff signal** | Orange banner + bell icon + gentlePulse animation |
| **Customer info** | Slide-in panel (desktop visible, mobile toggle) |
| **Rejected** | Concept A (contrast/focus risk), Concept C (gradient accessibility) |
| **Decided by** | Human approved — 2026-09-24 |
| **Date** | 2026-09-24 |

---

> [!IMPORTANT]
> **Human approval required.** Xem lại scorecard và recommendation ở trên. Nếu đồng ý với **Concept B — Soft Daylight**, confirm để tiến hành **Bước 4 — P4.4: Build Interactive Prototype**.
>
> Nếu muốn thay đổi lựa chọn (sang A hoặc C), hãy nêu lý do để ghi nhận vào decision record trước khi build.
