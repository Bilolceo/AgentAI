"""AIService orchestration tests (mock provider + stub retriever, no DB)."""
from __future__ import annotations

import pytest

from app.services.ai.provider import MockAIProvider
from app.services.ai.service import AIService
from app.services.knowledge.service import KBMatch
from app.services.safety.guard import SafetyAction


class StubKnowledge:
    def __init__(self, chunks: list[str]) -> None:
        self._matches = [
            KBMatch(id=i + 1, title=f"item-{i + 1}", content=c, category="faq")
            for i, c in enumerate(chunks)
        ]

    async def search(self, query: str, language: str, intent=None) -> list[KBMatch]:
        return list(self._matches)


def make_service(chunks: list[str] | None = None) -> AIService:
    return AIService(provider=MockAIProvider(), knowledge=StubKnowledge(chunks or []))


@pytest.mark.asyncio
async def test_safe_question_answers_from_kb() -> None:
    svc = make_service(chunks=["Klinika 9:00 dan 18:00 gacha ishlaydi."])
    result = await svc.respond(history=[], user_text="Ish vaqti qanday?", language="uz-UZ")
    assert result.action is SafetyAction.ALLOW
    assert not result.transfer_requested
    assert "9:00" in result.reply


@pytest.mark.asyncio
async def test_emergency_bypasses_provider() -> None:
    svc = make_service(chunks=["should not be used"])
    result = await svc.respond(
        history=[], user_text="Nafas ololmayapman", language="uz-UZ"
    )
    assert result.action is SafetyAction.EMERGENCY
    assert result.transfer_requested
    assert "103" in result.reply


@pytest.mark.asyncio
async def test_medicine_request_transfers() -> None:
    svc = make_service()
    result = await svc.respond(
        history=[], user_text="Qaysi dori ichsam bo'ladi?", language="uz-UZ"
    )
    assert result.action is SafetyAction.TRANSFER
    assert result.transfer_requested


@pytest.mark.asyncio
async def test_negative_talk_safe_reply_no_transfer_no_llm() -> None:
    # Provider returns this if (wrongly) called — assert it is NOT used.
    svc = make_service(chunks=["PROVIDER_WAS_CALLED"])
    result = await svc.respond(
        history=[], user_text="Falon klinika yomonmi?", language="uz-UZ"
    )
    assert result.action is SafetyAction.SAFE_REPLY
    assert not result.transfer_requested
    assert "PROVIDER_WAS_CALLED" not in result.reply


@pytest.mark.asyncio
async def test_low_confidence_transfers_after_generation() -> None:
    svc = make_service(chunks=["Klinika 9:00-18:00."])
    result = await svc.respond(
        history=[], user_text="Ish vaqti?", language="uz-UZ", ai_confidence=0.2
    )
    assert result.action is SafetyAction.TRANSFER
    assert result.transfer_requested


@pytest.mark.asyncio
async def test_high_confidence_returns_normal_reply() -> None:
    svc = make_service(chunks=["Klinika 9:00-18:00."])
    result = await svc.respond(
        history=[], user_text="Ish vaqti?", language="uz-UZ", ai_confidence=0.95
    )
    assert result.action is SafetyAction.ALLOW
    assert "9:00" in result.reply
