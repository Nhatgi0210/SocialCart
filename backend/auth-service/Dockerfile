FROM python:3.11-slim

WORKDIR /app

# Copy shared package
COPY backend/shared ./shared

# Copy service
COPY backend/auth-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/auth-service/app ./app

ENV PYTHONPATH=/app

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
