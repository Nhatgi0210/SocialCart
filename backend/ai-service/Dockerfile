FROM python:3.11-slim

WORKDIR /app
COPY backend/shared ./shared
COPY backend/ai-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ai-service/app ./app

ENV PYTHONPATH=/app
EXPOSE 8006
CMD ["uvicorn", "app.main:app", "--no-access-log", "--host", "0.0.0.0", "--port", "8006"]
