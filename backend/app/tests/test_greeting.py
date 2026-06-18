"""A3: greeting + language detection for the text simulation."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript import Transcript
from app.services.ai.provider import AIProvider, AIRequest
from app.services.ai.service import AIService
from app.services.audit.log import AuditLogService
from app.services.call.session import CallSessionService
from app.services.greeting import (
    GREETING_BILINGUAL,
    GREETING_RU,
    GREETING_UZ,
    GreetingService,
)
from app.services.language import Language, LanguageDetectionService
from app.services.operator.availability import MockOperatorAvailability
from app.services.operator.transfer import OperatorTransferDecisionService
from app.services.safety.reviewer import DeterministicSafetyValidator
from app.tests.test_call_session import make_service

detector = LanguageDetectionService()
greeter = GreetingService()
validator = DeterministicSafetyValidator()


# === Language detection ======================================================
def test_detect_uzbek() -> None:
    d = detector.detect("Assalomu alaykum, klinika qayerda joylashgan?")
    assert d.language is Language.UZ
    assert d.is_mixed is False


def test_detect_russian() -> None:
    d = detector.detect("Здравствуйте, где находится клиника?")
    assert d.language is Language.RU
    assert d.is_mixed is False


def test_detect_mixed() -> None:
    d = detector.detect("Доктор, menga yordam kerak iltimos")
    assert d.is_mixed is True
    assert d.language in (Language.UZ, Language.RU)


def test_detect_unknown() -> None:
    assert detector.detect("12345 !!! ???").language is Language.UNKNOWN


def test_from_code_parsing() -> None:
    assert Language.from_code("uz") is Language.UZ
    assert Language.from_code("ru-RU") is Language.RU
    assert Language.from_code(None) is None
    assert Language.from_code("en") is None


# === Greeting service ========================================================
def test_greeting_uz() -> None:
    assert greeter.greet(Language.UZ) == GREETING_UZ


def test_greeting_ru() -> None:
    assert greeter.greet(Language.RU) == GREETING_RU


def test_greeting_unknown_is_bilingual() -> None:
    g = greeter.greet(Language.UNKNOWN)
    assert g == GREETING_BILINGUAL
    assert GREETING_UZ in g and GREETING_RU in g


@pytest.mark.parametrize("greeting", [GREETING_UZ, GREETING_RU, GREETING_BILINGUAL])
def test_greeting_has_no_medical_advice(greeting: str) -> None:
    assert validator.validate(greeting, "uz-UZ").is_safe is True


# === Call start flow =========================================================
@pytest.mark.asyncio
async def test_start_call_uz_greeting(db_session: AsyncSession) -> None:
    svc = make_service(db_session)
    start = await svc.start_call(from_number="+998901112233", to_number="clinic", language_code="uz")
    assert start.language is Language.UZ
    assert start.greeting == GREETING_UZ
    assert start.call.language == "uz-UZ"


@pytest.mark.asyncio
async def test_start_call_ru_greeting(db_session: AsyncSession) -> None:
    svc = make_service(db_session)
    start = await svc.start_call(from_number="+79001112233", to_number="clinic", language_code="ru")
    assert start.language is Language.RU
    assert start.greeting == GREETING_RU
    assert start.call.language == "ru-RU"


@pytest.mark.asyncio
async def test_start_call_unknown_bilingual(db_session: AsyncSession) -> None:
    svc = make_service(db_session)
    start = await svc.start_call(from_number="+998901112233", to_number="clinic")
    assert start.language is Language.UNKNOWN
    assert start.greeting == GREETING_BILINGUAL
    assert start.call.language is None


@pytest.mark.asyncio
async def test_transcript_includes_greeting(db_session: AsyncSession) -> None:
    svc = make_service(db_session)
    start = await svc.start_call(from_number="+998901112233", to_number="clinic", language_code="uz")
    rows = await db_session.scalars(
        select(Transcript).where(Transcript.call_id == start.call.id)
    )
    transcripts = list(rows)
    assert len(transcripts) == 1
    assert transcripts[0].role == "assistant"
    assert transcripts[0].text == GREETING_UZ


@pytest.mark.asyncio
async def test_first_message_updates_session_language(db_session: AsyncSession) -> None:
    svc = make_service(db_session)
    # Start with unknown language (bilingual greeting), then caller speaks Russian.
    start = await svc.start_call(from_number="+998901112233", to_number="clinic")
    assert start.call.language is None

    outcome = await svc.handle_message(
        call_id=start.call.id, text="Здравствуйте, где вы находитесь?"
    )
    assert outcome.language == "ru-RU"
    await db_session.refresh(start.call)
    assert start.call.language == "ru-RU"


# === Safety after greeting ===================================================
class RaisingProvider(AIProvider):
    async def generate(self, request: AIRequest) -> str:
        raise AssertionError("LLM must not be called for emergency input")


@pytest.mark.asyncio
async def test_emergency_after_greeting_bypasses_llm(db_session: AsyncSession) -> None:
    audit = AuditLogService(db_session)
    ai = AIService(provider=RaisingProvider(), knowledge=_EmptyKnowledge())
    operator = OperatorTransferDecisionService(db_session, MockOperatorAvailability(), audit)
    svc = CallSessionService(db_session, ai, audit, operator)

    start = await svc.start_call(from_number="+998901112233", to_number="clinic", language_code="uz")
    outcome = await svc.handle_message(call_id=start.call.id, text="Nafas ololmayapman!")
    assert outcome.action == "emergency"
    assert "103" in outcome.reply


class _EmptyKnowledge:
    async def search(self, query: str, language: str, intent=None) -> list:
        return []
