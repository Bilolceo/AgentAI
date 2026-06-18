"""Async SQLAlchemy engine va session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Barcha modellar uchun deklarativ baza."""


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — request scope'li DB session."""
    async with SessionLocal() as session:
        yield session
