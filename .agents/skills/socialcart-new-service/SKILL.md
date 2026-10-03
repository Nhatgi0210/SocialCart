---
name: socialcart-new-service
description: >-
  Huong dan tung buoc tao mot microservice moi cho du an SocialCart. Su dung
  khi nguoi dung yeu cau them service moi, implement endpoint moi, hoac can
  scaffold cau truc service theo chuan cua du an. Bao gom cau truc thu muc,
  models, schemas, crud, routes va dang ky vao api-gateway.
---

# Tao Microservice Moi Cho SocialCart

## Buoc 1: Tao cau truc thu muc

```
backend/<service-name>/
    __init__.py
    main.py
    models.py
    schemas.py
    crud.py
    dependencies.py
    routes/
        __init__.py
        <resource>.py
    services/
        __init__.py
        <domain>.py
    requirements.txt
    Dockerfile
```

## Buoc 2: main.py template

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import resource_router
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ServiceName Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resource_router, prefix="/resource", tags=["resource"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "service-name"}
```

## Buoc 3: models.py (SQLAlchemy)

```python
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class ModelName(Base):
    __tablename__ = "table_name"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Buoc 4: schemas.py (Pydantic)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ModelBase(BaseModel):
    pass

class ModelCreate(ModelBase):
    pass

class ModelUpdate(BaseModel):
    pass

class ModelResponse(ModelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## Buoc 5: Dang ky port moi

- Them service vao docker-compose.yml voi port moi (xem Service Map trong socialcart-architecture skill)
- Them route vao api-gateway (backend/api-gateway/routes.py)

## Buoc 6: Kiem tra

1. Chay service doc lap: `uvicorn main:app --port PORT`
2. Kiem tra /health endpoint tra ve {"status": "ok"}
3. Kiem tra Swagger UI tai http://localhost:PORT/docs
4. Test qua api-gateway: http://localhost:8000/SERVICE-PREFIX/health
