"""Test fixtures — in-memory async SQLite session.

Only the relational tables are created (the pgvector `knowledge_chunks` table is
skipped — SQLite has no vector type). RAG is injected as a stub in tests that
need it, so the knowledge table is not required.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.db import Base
from app.models.admin_user import AdminUser
from app.models.audio_recording import AudioRecording
from app.models.audit_log import AuditLog
from app.models.booking import Booking
from app.models.call import Call
from app.models.callback_task import CallbackTask
from app.models.customer import Customer
from app.models.knowledge_item import KnowledgeItem
from app.models.telephony_call import TelephonyCall
from app.models.telephony_stream import TelephonyStream
from app.models.transcript import Transcript

@pytest.fixture(autouse=True)
def _reset_auth_attempts():
    """Keep lockout state and the injectable clock isolated between tests."""
    from app.services.auth.attempts import AuthAttemptService, reset_clock

    AuthAttemptService.reset_all()
    reset_clock()
    yield
    AuthAttemptService.reset_all()
    reset_clock()


_TABLES = [
    Customer.__table__,
    Call.__table__,
    Transcript.__table__,
    Booking.__table__,
    AuditLog.__table__,
    CallbackTask.__table__,
    KnowledgeItem.__table__,
    AdminUser.__table__,
    AudioRecording.__table__,
    TelephonyCall.__table__,
    TelephonyStream.__table__,
]


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=_TABLES))

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()
