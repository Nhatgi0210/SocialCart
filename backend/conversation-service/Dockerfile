FROM python:3.11-slim

WORKDIR /app

# Copy shared package
COPY backend/shared ./shared

# Copy service
COPY backend/conversation-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/conversation-service/app ./app

ENV PYTHONPATH=/app

EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
