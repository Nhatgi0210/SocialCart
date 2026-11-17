FROM python:3.11-slim

WORKDIR /app
COPY backend/shared ./shared
COPY backend/order-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/order-service/app ./app

ENV PYTHONPATH=/app
EXPOSE 8005
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
