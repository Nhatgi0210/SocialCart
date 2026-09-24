# Hướng dẫn áp dụng Chapter 4 — AI for Product Design vào SocialCart

## Tổng quan

Chapter 4 cung cấp 5 file prompt có sẵn trong thư mục
[`chapter-04-ai-for-product-design/prompts/`](../../chapter-04-ai-for-product-design/prompts/).
Bạn **dùng lại nguyên các file đó**, chỉ thay **Inputs** và **đường dẫn output** cho SocialCart.

> [!IMPORTANT]
> Mỗi bước chạy trong **fresh session** mới. Không dùng lại session cũ để tránh
> AI bị ảnh hưởng bởi context thừa.

---

## Quy trình

```
P4.1 → HUMAN CHECK → P4.2 → P4.3 (Review Gate) → P4.4 → P4.5 (Review Gate)
```

---

## Bước 1 — P4.1: Tạo Product Design Brief

**Prompt gốc:** [`create-product-design-brief.prompt.md`](../../chapter-04-ai-for-product-design/prompts/create-product-design-brief.prompt.md)

**Cách dùng cho SocialCart — chỉ thay phần Inputs:**

| Trường trong prompt gốc | Giá trị cho SocialCart |
|---|---|
| `Product requirements` | [`docs/product-requirements.md`](product-requirements.md) |
| `Feature specification` | [`docs/feature-specification.md`](feature-specification.md) |
| Human visual references | References bạn đã inspect (xem HUMAN CHECK bên dưới) |

**Thay phần Task** — Ở đoạn `## Task` của prompt gốc, nó nói *"ticket contract, four-status board, lane/global creation..."* — bạn thêm một dòng chỉ định scope cho SocialCart:

```
Scope prototype: Unified Inbox + Chat với AI + Quick Order creation.
Thay vì board kanban, design brief phải cover:
- User struggle: người bán bỏ sót tin nhắn từ nhiều nền tảng
- Conversation list contract (platform badge, unread, status label)
- Chat view contract (AI message, human message, typing indicator, handoff)
- Order creation contract (quick order modal từ chat)
- States: loading, AI failure + retry, empty inbox, narrow view, reduced motion
```

**Thay phần Save or update:**
```
Sau khi approve, lưu vào: SocialCart/docs/product-design-brief.md
```

**Output:** [`docs/product-design-brief.md`](product-design-brief.md) ← tạo mới

---

## HUMAN CHECK (Bắt buộc — sau P4.1, trước P4.2)

> [!WARNING]
> **Không được bỏ qua.** AI không thể thay bạn inspect reference thật.

Việc bạn phải làm:
1. **Inspect 3–5 app thật**, ví dụ: Intercom, Tidio, Crisp, Shopee Seller Center
2. **Ghi lại cụ thể những gì bạn quan sát** — không chỉ lưu link:
   - Layout: sidebar trái / chat giữa / info panel phải?
   - AI badge trông như thế nào? Typing indicator?
   - UI chuyển từ AI → người bán ra sao?
   - Tạo đơn từ chat: modal hay side panel?
3. **Chốt visual direction** muốn khám phá (dark/light/glass/minimal...)

---

## Bước 2 — P4.2: Explore Interface Directions

**Prompt gốc:** [`explore-interface-directions.prompt.md`](../../chapter-04-ai-for-product-design/prompts/explore-interface-directions.prompt.md)

**Cách dùng cho SocialCart — thay phần Inputs:**

| Trường trong prompt gốc | Giá trị cho SocialCart |
|---|---|
| `Accepted design brief` | [`docs/product-design-brief.md`](product-design-brief.md) |
| `Directly inspected interaction patterns` | Observations bạn ghi được ở HUMAN CHECK |
| `Human decisions about concepts to compare` | Visual directions bạn muốn so sánh |

**Thay phần Constraints** — Ở đoạn `- Keep auth, ticket, lane...` thay bằng:
```
Keep: conversation list, chat view, AI indicator, handoff, order modal behavior comparable across concepts.
Do not add: metrics dashboard, analytics, inventory management, shipping integration.
```

**Thay phần Save or update:**
```
Lưu vào: SocialCart/design/concepts/concept-a.html, concept-b.html, concept-c.html
```

**Output:**
```
SocialCart/design/concepts/concept-a.html
SocialCart/design/concepts/concept-b.html
SocialCart/design/concepts/concept-c.html
```

---

## Bước 3 — P4.3: Critique and Select (Review Gate)

**Prompt gốc:** [`critique-and-select-interface.prompt.md`](../../chapter-04-ai-for-product-design/prompts/critique-and-select-interface.prompt.md)

**Cách dùng cho SocialCart — thay phần Inputs:**

| Trường trong prompt gốc | Giá trị cho SocialCart |
|---|---|
| `Accepted design brief` | [`docs/product-design-brief.md`](product-design-brief.md) |
| `Concepts` | `SocialCart/design/concepts/` |
| `Human review notes` | Quan sát của bạn khi xem qua 3 concept |

**Thay phần Task** — Thay danh sách audit items từ Kanban sang SocialCart:
```
Compare: inbox scanability (unread badge, platform icon FB/Zalo, last message preview),
chat clarity (AI vs human message distinction, typing indicator, handoff signal),
order action accessibility (quick order modal từ chat),
focus order, keyboard navigation, narrow viewport, reduced motion, recovery states.
```

**Thay phần Save or update:**
```
Sau khi approve, lưu decision vào: SocialCart/docs/product-design.md
```

**Output:** [`docs/product-design.md`](product-design.md) ← tạo mới sau khi bạn approve

---

## Bước 4 — P4.4: Build Interactive Prototype

**Prompt gốc:** [`build-interactive-prototype.prompt.md`](../../chapter-04-ai-for-product-design/prompts/build-interactive-prototype.prompt.md)

**Cách dùng cho SocialCart — thay phần Inputs:**

| Trường trong prompt gốc | Giá trị cho SocialCart |
|---|---|
| `Accepted design brief` | [`docs/product-design-brief.md`](product-design-brief.md) |
| `Accepted direction` | [`docs/product-design.md`](product-design.md) |
| `User flow` | `SocialCart/design/user-flow.mmd` (tạo ở bước này) |
| `Selected concept` | File concept đã chọn ở P4.3 |

**Thay phần Task** — Thay nội dung build từ Kanban board sang SocialCart:
```
Build:
- Login / simulated auth
- Unified Inbox: danh sách hội thoại (Facebook + Zalo mock data), unread badge, platform icon, status label
- Chat view: AI message, human message, AI typing indicator
- AI → Human handoff: button + state change rõ ràng
- Quick order creation modal từ chat
- Empty inbox state với action rõ ràng
- Simulated AI failure + retry behavior
```

**Thay phần Expected output:**
```
SocialCart/prototype/index.html
SocialCart/prototype/styles.css
SocialCart/prototype/mock-data.js
SocialCart/prototype/app.js
```

---

## Bước 5 — P4.5: Review Interactive Prototype (Review Gate)

**Prompt gốc:** [`review-interactive-prototype.prompt.md`](../../chapter-04-ai-for-product-design/prompts/review-interactive-prototype.prompt.md)

**Cách dùng cho SocialCart — thay phần Inputs:**

| Trường trong prompt gốc | Giá trị cho SocialCart |
|---|---|
| `Accepted design brief` | [`docs/product-design-brief.md`](product-design-brief.md) |
| `Selected design` | [`docs/product-design.md`](product-design.md) |
| `Running static prototype` | `SocialCart/prototype/` |

**Thay phần Task** — Thay flow audit từ Kanban sang SocialCart:
```
Capture flow:
login → inbox list → mở conversation → xem AI response → trigger handoff → tạo order từ chat → empty inbox state → simulated AI failure + retry

Với mỗi issue: evidence, impact, affected interaction, smallest correction.
```

**Thay phần Save or update:**
```
Sau khi human review, cập nhật corrections vào: SocialCart/docs/product-design.md
```

---

## Cấu trúc thư mục sau khi hoàn thành

```
SocialCart/
├── docs/
│   ├── product-requirements.md        ✅ có sẵn
│   ├── feature-specification.md       ✅ có sẵn
│   ├── product-design-brief.md        ← P4.1 output
│   └── product-design.md              ← P4.3 tạo, P4.5 cập nhật
├── design/
│   ├── user-flow.mmd                  ← tạo cùng P4.1
│   └── concepts/
│       ├── concept-a.html             ← P4.2 output
│       ├── concept-b.html
│       └── concept-c.html
└── prototype/
    ├── index.html                     ← P4.4 output
    ├── styles.css
    ├── mock-data.js
    └── app.js
```

---

## Tóm tắt: Điều duy nhất bạn phải thay ở mỗi bước

| Bước | File prompt gốc | Thay gì |
|---|---|---|
| P4.1 | `create-product-design-brief.prompt.md` | Inputs (PRD/Spec paths) + scope task (Inbox/Chat/Order) + output path |
| P4.2 | `explore-interface-directions.prompt.md` | Inputs + constraint items + output path |
| P4.3 | `critique-and-select-interface.prompt.md` | Inputs + audit checklist items + output path |
| P4.4 | `build-interactive-prototype.prompt.md` | Inputs + build task list + output files |
| P4.5 | `review-interactive-prototype.prompt.md` | Inputs + audit flow + output path |

> [!NOTE]
> Mọi constraint khác trong prompt gốc — **giữ nguyên**. Đặc biệt:
> `dependency-free`, `backend-free`, `reset state on reload`,
> `do not record decision until human approves` — áp dụng y chang cho SocialCart.
