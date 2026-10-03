---
name: socialcart-dev-setup
description: >-
  Huong dan setup moi truong phat trien local cho SocialCart, bao gom cach chay
  tat ca services, cau hinh env, connect Facebook/Zalo webhook qua ngrok, va
  cac lenh hay dung hang ngay. Su dung khi nguoi dung can chay du an local
  hoac khi co van de voi moi truong phat trien.
---

# SocialCart Dev Setup

## Yeu cau he thong

- Python 3.11+
- Node.js 18+
- MySQL 8.0 (local hoac Docker)
- Redis 7 (local hoac Docker)
- ngrok (de test webhook)

## Buoc 1: Chay Infrastructure qua Docker

```bash
docker-compose up -d mysql redis
docker ps  # Kiem tra container dang chay
```

## Buoc 2: Setup Backend

```bash
# Tao virtual env
python -m venv venv
venv\Scripts\activate  # Windows

# Cai dat requirements tung service
cd backend/auth-service && pip install -r requirements.txt
cd ../conversation-service && pip install -r requirements.txt
# ... tuong tu cac service khac
```

## Buoc 3: Cau hinh .env

Tao file `.env` tai root:

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/socialcart
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
FB_APP_ID=your-fb-app-id
FB_APP_SECRET=your-fb-app-secret
FB_VERIFY_TOKEN=your-verify-token
ZALO_APP_ID=your-zalo-app-id
ZALO_APP_SECRET=your-zalo-app-secret
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-pro
AUTH_SERVICE_URL=http://localhost:8001
CONVERSATION_SERVICE_URL=http://localhost:8002
CUSTOMER_SERVICE_URL=http://localhost:8003
PRODUCT_SERVICE_URL=http://localhost:8004
ORDER_SERVICE_URL=http://localhost:8005
AI_SERVICE_URL=http://localhost:8006
REALTIME_SERVICE_URL=http://localhost:8009
PLATFORM_SERVICE_URL=http://localhost:8010
```

## Buoc 4: Chay Services

Mo 11 terminal, moi terminal chay 1 service:

```bash
# api-gateway (:8000)
cd backend/api-gateway && uvicorn main:app --port 8000 --reload

# auth-service (:8001)
cd backend/auth-service && uvicorn main:app --port 8001 --reload

# conversation-service (:8002)
cd backend/conversation-service && uvicorn main:app --port 8002 --reload

# customer-service (:8003)
cd backend/customer-service && uvicorn main:app --port 8003 --reload

# product-service (:8004)
cd backend/product-service && uvicorn main:app --port 8004 --reload

# order-service (:8005)
cd backend/order-service && uvicorn main:app --port 8005 --reload

# ai-service (:8006)
cd backend/ai-service && uvicorn main:app --port 8006 --reload

# webhook-service (:8007)
cd backend/webhook-service && uvicorn main:app --port 8007 --reload

# dashboard-service (:8008)
cd backend/dashboard-service && uvicorn main:app --port 8008 --reload

# realtime-service (:8009)
cd backend/realtime-service && uvicorn main:app --port 8009 --reload

# platform-service (:8010)
cd backend/platform-service && uvicorn main:app --port 8010 --reload

# Celery Worker (ai-service)
cd backend/ai-service && celery -A celery_app worker --loglevel=info

# Frontend
cd frontend && npm install && npm run dev
```

## Buoc 5: Webhook qua ngrok

```bash
ngrok http 8000
# Copy HTTPS URL vi du: https://abc123.ngrok.io

# Facebook Developer Console:
# Webhook URL: https://abc123.ngrok.io/webhooks/facebook
# Verify Token: gia tri FB_VERIFY_TOKEN trong .env

# Zalo OA Dashboard:
# Webhook URL: https://abc123.ngrok.io/webhooks/zalo
```

## Lenh Debug Hay Dung

```bash
# Kiem tra tat ca services health
for port in 8000 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010; do
    echo "Port $port:" && curl -s http://localhost:$port/health
done

# Xem Celery tasks dang chay
cd backend/ai-service && celery -A celery_app inspect active

# Reset DB
mysql -u root -p -e "DROP DATABASE socialcart; CREATE DATABASE socialcart;"
python backend/scripts/init_db.py

# Chay tests
pytest backend/tests/ -v
```

## Debug Tips

- Webhook khong nhan duoc: Kiem tra ngrok URL da duoc set trong FB/Zalo console chua
- AI khong tra loi: Kiem tra GEMINI_API_KEY, xem Celery worker co dang chay khong
- Realtime khong hoat dong: Kiem tra CORS va port 8009 co duoc allow tu frontend chua
- DB connection error: Kiem tra MySQL container dang chay va DATABASE_URL dung format
