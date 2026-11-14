FROM python:3.11-slim

WORKDIR /app

# Copy shared package
COPY backend/shared ./shared

# Copy service
COPY backend/product-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/product-service/app ./app

ENV PYTHONPATH=/app

EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
