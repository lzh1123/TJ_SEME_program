from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..settings import settings


class Base(DeclarativeBase):
    pass


# ── Async engine (used by the app at runtime) ──
async_engine = create_async_engine(settings.database_url, echo=settings.database_echo)

async_session_factory = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


# ── Sync engine (used by Alembic migrations) ──
sync_engine = create_engine(settings.database_url_sync, echo=settings.database_echo)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency that yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
