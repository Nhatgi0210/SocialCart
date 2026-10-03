---
name: socialcart-order-flow
description: >-
  Mo ta vong doi don hang (Order Lifecycle) cua SocialCart: cac trang thai,
  business rules chuyen doi trang thai, inventory hold/release mechanism,
  VietQR payment generation va cach xu ly edge cases. Su dung khi implement
  order-related features hoac xu ly loi lien quan den don hang.
---

# SocialCart Order Lifecycle

## Cac Trang Thai Don Hang

```
pending_confirm -> confirmed -> shipping -> completed
                             -> cancelled
pending_confirm              -> cancelled
```

| Trang thai | Mo ta | Nguoi thuc hien |
|------------|-------|-----------------|
| pending_confirm | Don nhap tu AI, cho xac nhan | AI tao, nguoi ban xac nhan |
| confirmed | Da xac nhan, chuan bi hang | Nguoi ban |
| shipping | Dang giao hang | Nguoi ban |
| completed | Giao thanh cong | Nguoi ban |
| cancelled | Da huy | Nguoi ban (bat ky giai doan) |

## Business Rules

1. Inventory Hold: Khi order chuyen sang pending_confirm, lock so luong (variant.hold_quantity += quantity)
2. Inventory Release: Khi order bi cancelled, giai phong so luong da hold
3. Inventory Deduct: Khi order chuyen sang confirmed, tru thuc su tu kho
4. Khong allow confirmed neu het hang: Kiem tra stock truoc khi confirm
5. AI chi tao pending_confirm: AI KHONG DUOC tu chuyen sang confirmed

## Order Model

```python
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    status = Column(Enum("pending_confirm","confirmed","shipping","completed","cancelled"))
    total_amount = Column(Numeric(12, 2))
    shipping_fee = Column(Numeric(10, 2), default=0)
    payment_status = Column(Enum("unpaid","paid","refunded"), default="unpaid")
    shipping_name = Column(String(200))
    shipping_phone = Column(String(20))
    shipping_address = Column(Text)
    note = Column(Text, nullable=True)
    created_by = Column(Enum("ai", "seller"))
    created_at = Column(DateTime, default=datetime.utcnow)
```

## VietQR Payment URL

```python
def generate_vietqr_url(order, bank_config: dict) -> str:
    amount = int(order.total_amount + order.shipping_fee)
    order_ref = f"DH{order.id:06d}"
    bank_code = bank_config["bank_code"]
    account = bank_config["account_number"]
    account_name = bank_config["account_name"]
    return (
        f"https://img.vietqr.io/image/{bank_code}-{account}-compact2.png"
        f"?amount={amount}&addInfo={order_ref}&accountName={account_name}"
    )
```

## API Endpoints (order-service :8005)

```
GET    /orders                  List orders, filter by status/customer
GET    /orders/{id}             Order detail
POST   /orders                  Tao order moi (tu AI hoac nguoi ban)
PATCH  /orders/{id}/status      Chuyen trang thai
DELETE /orders/{id}             Huy don (set status = cancelled)
GET    /orders/{id}/payment-qr  Lay VietQR URL
```

## Edge Cases Can Xu Ly

- Khach huy sau khi da confirmed: Giai phong inventory, hoi lai ly do
- San pham het hang khi confirm: Block confirm, thong bao nguoi ban
- Thay doi dia chi sau confirmed: Cho phep update neu chua shipping
- Don trung lap: Neu cung customer cung san pham trong 5 phut, canh bao nguoi ban
- Don gia tri 0: Khong cho phep tao don co total_amount = 0
