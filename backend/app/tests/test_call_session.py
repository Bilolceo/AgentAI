"""CallSessionService lifecycle + transfer tests (in-memory SQLite)."""
from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.transcript import Transcript
from app.services.ai.provider import MockAIProvider
from app.services.ai.service import AIService
from app.services.audit.log import AuditLogService
from app.services.call.session import CallSessionService
from app.services.knowledge.service import KBMatch
from app.services.operator.availability import MockOperatorAvailability, OperatorState
from app.services.operator.transfer import OperatorTransferDecisionService


class StubKnowledge:
    def __init__(self, chunks: list[str]) -> None:
        self._matches = [
            KBMatch(id=i + 1, title=f"item-{i + 1}", content=c, category="faq")
            for i, c in enumerate(chunks)
        ]

    async def search(self, query: str, language: str, intent=None) -> list[KBMatch]:
        return list(self._matches)


def make_service(
    session: AsyncSession,
    chunks: list[str] | None = None,
    operator_state: OperatorState = OperatorState.AVAILABLE,
) -> CallSessionService:
    ai = AIService(provider=MockAIProvider(), knowledge=StubKnowledge(chunks or []))
    audit = AuditLogService(session)
    operator = OperatorTransferDecisionService(
        session, MockOperatorAvailability(operator_state), audit
    )
    return CallSessionService(session, ai, audit, operator)


@pytest.mark.asyncio
async def test_full_lifecycle_safe_question(db_session: AsyncSession) -> None:
    svc = make_service(db_session, chunks=["Klinika 9:00-18:00 ishlaydi."])
    call = (await svc.start_call(from_number="+998901112233", to_number="clinic")).call

    outcome = await svc.handle_message(call_id=call.id, text="Ish vaqtingiz qanday?")
    assert outcome.action == "allow"
    assert not outcome.transferred
    assert outcome.language == "uz-UZ"

    # greeting (assistant) + user + assistant transcripts saved.
    count = await db_session.scalar(
        select(func.count()).select_from(Transcript).where(Transcript.call_id == call.id)
    )
    assert count == 3

    ended = await svc.end_call(call_id=call.id)
    assert ended.status == "completed"
    assert ended.ended_at is not None


@pytest.mark.asyncio
async def test_emergency_transfers_and_marks_call(db_session: AsyncSession) -> None:
    svc = make_service(db_session)
    call = (await svc.start_call(from_number="+998901112233", to_number="clinic")).call

    outcome = await svc.handle_message(call_id=call.id, text="Nafas ololmayapman!")
    assert outcome.action == "emergency"
    assert outcome.transferred
    assert "103" in outcome.reply

    await db_session.refresh(call)
    assert call.status == "transferred"

    # Audit trail recorded the transfer.
    events = await db_session.scalars(
        select(AuditLog.event).where(AuditLog.call_id == call.id)
    )
    event_set = set(events.all())
    assert "operator_transfer_requested" in event_set
    assert "safety_guard_triggered" in event_set


@pytest.mark.asyncio
async def test_russian_language_detected(db_session: AsyncSession) -> None:
    svc = make_service(db_session, chunks=["Клиника работает с 9 до 18."])
    call = (await svc.start_call(from_number="+79001112233", to_number="clinic")).call
    outcome = await svc.handle_message(call_id=call.id, text="Какие часы работы?")
    assert outcome.language == "ru-RU"
    assert outcome.action == "allow"


@pytest.mark.asyncio
async def test_unknown_call_raises(db_session: AsyncSession) -> None:
    svc = make_service(db_session)
    with pytest.raises(ValueError):
        await svc.handle_message(call_id=99999, text="salom")
