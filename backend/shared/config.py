"""
Cấu hình chung cho tất cả service SocialCart.
Đọc từ biến môi trường (hoặc .env ở root project).

Mỗi service chỉ đọc các trường mình cần; không require credential không liên quan.
"""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình chia sẻ giữa các service."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",  # mỗi service chỉ dùng phần mình cần
    )

    # ── Môi trường ──────────────────────────────────────────────────────────
    app_env: str = Field(default="local", alias="APP_ENV")

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="mysql+aiomysql://socialcart:CHANGE_ME_LOCAL_ONLY@127.0.0.1:3306/socialcart_db",
        alias="DATABASE_URL",
    )

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="REDIS_URL")

    # ── JWT / Auth ───────────────────────────────────────────────────────────
    jwt_algorithm: str = Field(default="RS256", alias="JWT_ALGORITHM")
    jwt_private_key_path: str = Field(default="./keys/private.pem", alias="JWT_PRIVATE_KEY_PATH")
    jwt_public_key_path: str = Field(default="./keys/public.pem", alias="JWT_PUBLIC_KEY_PATH")
    jwt_issuer: str = Field(default="socialcart-auth", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="socialcart-api", alias="JWT_AUDIENCE")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    session_idle_timeout_seconds: int = Field(default=86400, alias="SESSION_IDLE_TIMEOUT_SECONDS")
    refresh_cookie_secure: bool = Field(default=False, alias="REFRESH_COOKIE_SECURE")

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_allowed_origins: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        alias="CORS_ALLOWED_ORIGINS",
    )

    # ── Service-to-service ───────────────────────────────────────────────────
    internal_service_token: str = Field(default="", alias="INTERNAL_SERVICE_TOKEN")

    # ── Platform flags (service chỉ đọc khi cần) ────────────────────────────
    facebook_enabled: bool = Field(default=False, alias="FACEBOOK_ENABLED")
    zalo_enabled: bool = Field(default=False, alias="ZALO_ENABLED")
    ai_enabled: bool = Field(default=False, alias="AI_ENABLED")

    # ── Internal service URLs ────────────────────────────────────────────────
    auth_service_url: str = Field(default="http://127.0.0.1:8001", alias="AUTH_SERVICE_URL")
    conversation_service_url: str = Field(default="http://127.0.0.1:8002", alias="CONVERSATION_SERVICE_URL")
    customer_service_url: str = Field(default="http://127.0.0.1:8003", alias="CUSTOMER_SERVICE_URL")
    product_service_url: str = Field(default="http://127.0.0.1:8004", alias="PRODUCT_SERVICE_URL")
    order_service_url: str = Field(default="http://127.0.0.1:8005", alias="ORDER_SERVICE_URL")
    ai_service_url: str = Field(default="http://127.0.0.1:8006", alias="AI_SERVICE_URL")
    webhook_service_url: str = Field(default="http://127.0.0.1:8007", alias="WEBHOOK_SERVICE_URL")
    dashboard_service_url: str = Field(default="http://127.0.0.1:8008", alias="DASHBOARD_SERVICE_URL")
    realtime_service_url: str = Field(default="http://127.0.0.1:8009", alias="REALTIME_SERVICE_URL")
    platform_service_url: str = Field(default="http://127.0.0.1:8010", alias="PLATFORM_SERVICE_URL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Trả Settings singleton, cache sau lần đầu tiên."""
    return Settings()


# Shortcut tiện dụng cho import trực tiếp
settings = get_settings()
