"""
SQLAlchemy async session factory và dependency FastAPI.

Dùng aiomysql driver; pool được mở/đóng qua lifespan context của từng service.
Migration do Alembic quản lý; KHÔNG gọi Base.metadata.create_all() ở đây.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shared.config import settings

# ── Engine singleton ──────────────────────────────────────────────────────────
# Được tạo lúc import; pool thực sự kết nối khi có request đầu tiên.
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _make_engine() -> AsyncEngine:
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,      # phát hiện connection stale
        pool_recycle=1800,       # tái dùng sau 30 phút
        pool_size=10,
        max_overflow=20,
        echo=settings.app_env == "local",
    )


def get_engine() -> AsyncEngine:
    """Trả engine toàn cục (tạo nếu chưa có)."""
    global _engine
    if _engine is None:
        _engine = _make_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Trả session factory toàn cục."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
            class_=AsyncSession,
        )
    return _session_factory


# ── Lifespan helper cho FastAPI ───────────────────────────────────────────────

@asynccontextmanager
async def db_lifespan():
    """
    Dùng trong lifespan của FastAPI app:

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with db_lifespan():
                yield
    """
    # Khởi tạo pool (ping thực khi có query đầu tiên)
    get_engine()
    try:
        yield
    finally:
        engine = get_engine()
        await engine.dispose()


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency trả AsyncSession trong một request.

    Dùng:
        @router.get("/")
        async def handler(db: AsyncSession = Depends(get_session)):
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
