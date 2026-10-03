---
name: socialcart-webhook
description: >-
  Huong dan xu ly webhook tu Facebook Messenger va Zalo OA cho SocialCart.
  Su dung khi implement hoac debug webhook handlers, verify signatures,
  parse message payloads, hoac khi can them loai su kien webhook moi.
---

# SocialCart Webhook Integration

## Facebook Messenger Webhook

### Verify Challenge (GET)

```python
@router.get("/webhooks/facebook")
def verify_facebook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_verify_token == settings.FB_VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403)
```

### Nhan tin nhan (POST)

```python
@router.post("/webhooks/facebook")
async def facebook_webhook(request: Request):
    # 1. Verify X-Hub-Signature-256
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_facebook_signature(payload, signature, settings.FB_APP_SECRET):
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()
    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):
            if "message" in messaging:
                await handle_fb_message(messaging)
    return {"status": "ok"}
```

### Cau truc Facebook Message Event

```json
{
  "sender": {"id": "PSID_cua_khach"},
  "recipient": {"id": "PAGE_ID"},
  "timestamp": 1696000000000,
  "message": {
    "mid": "m_xxx",
    "text": "Noi dung tin nhan"
  }
}
```

## Zalo OA Webhook

### Cau truc Zalo Message Event

```json
{
  "event_name": "user_send_text",
  "user_id_by_app": "zalo_uid",
  "oa_id": "OA_ID",
  "timestamp": 1696000000000,
  "message": {
    "msg_id": "m_xxx",
    "text": "Noi dung tin nhan"
  }
}
```

## Xu ly chung sau khi parse

```python
async def handle_incoming_message(
    platform: str,
    platform_user_id: str,
    platform_conv_id: str,
    text: str,
    attachments: list
):
    # 1. Upsert customer
    customer = await customer_service.upsert(platform, platform_user_id)
    # 2. Upsert conversation
    conv = await conversation_service.upsert(customer.id, platform, platform_conv_id)
    # 3. Save message
    msg = await conversation_service.save_message(conv.id, "customer", text)
    # 4. Emit realtime
    await realtime_service.emit("message:new", conv.id)
    # 5. Queue AI task (neu AI mode = auto)
    if conv.ai_mode == "auto":
        process_ai_message.delay(conv.id, msg.id)
```

## Idempotency

- Moi webhook event phai duoc xu ly dung 1 lan
- Luu message_id (mid/msg_id) de detect duplicate
- Su dung Redis SET de track processed event IDs (TTL 24h)

```python
import redis
r = redis.Redis.from_url(settings.REDIS_URL)

def is_duplicate_event(event_id: str) -> bool:
    key = f"webhook:processed:{event_id}"
    return not r.set(key, 1, nx=True, ex=86400)
```
