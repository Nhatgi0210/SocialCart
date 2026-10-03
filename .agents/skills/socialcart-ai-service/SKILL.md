---
name: socialcart-ai-service
description: >-
  Huong dan chi tiet ve AI service cua SocialCart: Gemini 1.5 Pro integration,
  cach xu ly hoi thoai, FAQ config, intent detection va human-handoff mechanism.
  Su dung khi can implement hoac chinh sua logic AI tu dong xu ly tin nhan,
  tu van san pham, chot don, hoac cau hinh cac tinh huong AI.
---

# SocialCart AI Service

## Tong quan

- AI Model: Google Gemini 1.5 Pro API
- Port: 8006
- Worker: Celery (Redis backend)
- Trigger: Nhan task tu Redis Queue, duoc conversation-service publish

## Cau truc System Prompt

System prompt cho Gemini duoc xay dung dong tu:

1. Role: Tro ly AI ban hang cua [ten cua hang]
2. Products: Danh sach san pham + bien the + gia + ton kho thuc te
3. FAQs: Danh sach cau hoi va cau tra loi da cau hinh
4. Policies: Chinh sach van chuyen, doi tra, thanh toan
5. History: 20 tin nhan gan nhat cua cuoc hoi thoai
6. Constraints: Gioi han nhung gi AI co the lam

## Intent Detection

AI tra ve JSON kem noi dung tra loi:

```json
{
  "reply": "noi dung tra loi khach hang",
  "intent": "inquiry|buying_intent|ready_to_order|complaint|other",
  "confidence": 0.85,
  "extracted_order": {
    "product_id": null,
    "variant_id": null,
    "quantity": null,
    "customer_name": null,
    "phone": null,
    "address": null
  },
  "needs_human": false,
  "handoff_reason": null
}
```

## Dieu kien chuyen giao nguoi ban (Human-in-the-loop)

AI phai set needs_human=true khi:
- Khach hang yeu cau gap nguoi that
- Khieu nai phuc tap, hoan/tra hang
- Khach hoi ve giam gia / thuong luong
- AI confidence duoi 0.6 sau 2 lan thu
- Khach hoi thong tin AI khong co trong context

## Celery Task Flow

```python
@celery_app.task
def process_ai_message(conversation_id: int, message_id: int):
    # 1. Load context tu DB
    context = load_conversation_context(conversation_id)
    # 2. Build system prompt
    prompt = build_system_prompt(context)
    # 3. Call Gemini API
    result = call_gemini(prompt, context.history)
    # 4. Parse response JSON
    parsed = parse_ai_response(result)
    # 5. Save AI reply
    save_message(conversation_id, parsed["reply"], sender="ai")
    # 6. Update conversation intent/status
    update_conversation_intent(conversation_id, parsed["intent"])
    # 7. Neu can human: update conversation status -> needs_human
    if parsed["needs_human"]:
        set_conversation_needs_human(conversation_id, parsed["handoff_reason"])
    # 8. Send reply qua platform-service
    send_via_platform(conversation_id, parsed["reply"])
    # 9. Emit realtime
    emit_realtime("message:new", conversation_id)
```

## FAQ Config Schema

```json
{
  "faqs": [
    {
      "id": "faq_001",
      "trigger_keywords": ["ship", "giao hang", "van chuyen"],
      "question": "Phi ship bao nhieu?",
      "answer": "Phi ship tu 25.000d, mien phi don tren 500.000d"
    }
  ]
}
```

## Quan trong

- Khong bao gio AI tu dong xac nhan don hang (phai co human confirmation)
- Khong tra loi cac chu de ngoai pham vi ban hang
- Log tat ca Gemini API calls voi token count de theo doi chi phi
- Gioi han history: 20 tin nhan gan nhat de tranh vuot context window
