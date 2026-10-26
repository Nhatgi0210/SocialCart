FROM python:3.11-slim

WORKDIR /app

# Copy shared package
COPY backend/shared ./shared

# Copy service
COPY backend/api-gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/api-gateway/app ./app

# PYTHONPATH bao gồm /app để `from shared...` resolve được
ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
