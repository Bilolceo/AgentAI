"""A4: structured Knowledge Base — search, grounding, anti-hallucination."""
from __future__ import annotations

import re

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.provider import MockAIProvider
from app.services.ai.service import AIService
from app.services.knowledge.intent import KBIntent, classify_intent
from app.services.knowledge.seed import seed_demo_clinic
from app.services.knowledge.service import KBCategory, KnowledgeBaseService
from app.services.safety.guard import SafetyAction

_CYRILLIC = re.compile(r"[а-яё]", re.IGNORECASE)


async def _seeded_ai(db_session: AsyncSession) -> AIService:
    await seed_demo_clinic(db_session)
    kb = KnowledgeBaseService(db_session)
    return AIService(provider=MockAIProvider(), knowledge=kb)


# === Intent classification ===================================================
@pytest.mark.parametrize(
    "text,intent",
    [
        ("Klinika manzili qayerda?", KBIntent.ADDRESS),
        ("Konsultatsiya narxi qancha?", KBIntent.PRICE),
        ("Kardiolog qabul vaqti qachon?", KBIntent.SCHEDULE),
        ("Qaysi shifokorlar bor?", KBIntent.DOCTOR),
        ("Tahlilga qanday tayyorlanaman?", KBIntent.PREPARATION),
        ("Salom, yaxshimisiz?", KBIntent.GENERAL),
    ],
)
def test_classify_intent(text: str, intent: KBIntent) -> None:
    assert classify_intent(text) is intent


# === KB answers come from the KB =============================================
@pytest.mark.asyncio
async def test_clinic_address_from_kb(db_session: AsyncSession) -> None:
    ai = await _seeded_ai(db_session)
    r = await ai.respond(history=[], user_text="Klinika manzili qayerda?", language="uz-UZ")
    assert r.action is SafetyAction.ALLOW
    assert "Chilonzor" in r.reply
    assert r.sources and r.sources[0]["title"] == "Klinika manzili"


@pytest.mark.asyncio
async def test_service_price_from_kb(db_session: AsyncSession) -> None:
    ai = await _seeded_ai(db_session)
    r = await ai.respond(history=[], user_text="Konsultatsiya narxi qancha?", language="uz-UZ")
    assert r.action is SafetyAction.ALLOW
    assert "150 000" in r.reply
    assert r.sources


@pytest.mark.asyncio
async def test_doctor_schedule_from_kb(db_session: AsyncSession) -> None:
    ai = await _seeded_ai(db_session)
    r = await ai.respond(history=[], user_text="Kardiolog qabul vaqti qachon?", language="uz-UZ")
    assert r.action is SafetyAction.ALLOW
    assert "09:00-14:00" in r.reply


# === Anti-hallucination ======================================================
@pytest.mark.asyncio
async def test_unknown_price_transfers_to_operator(db_session: AsyncSession) -> None:
    ai = await _seeded_ai(db_session)
    r = await ai.respond(history=[], user_text="Rentgen narxi qancha?", language="uz-UZ")
    assert r.action is SafetyAction.TRANSFER
    assert r.transfer_requested
    assert r.sources == []


@pytest.mark.asyncio
async def test_unknown_doctor_does_not_hallucinate(db_session: AsyncSession) -> None:
    ai = await _seeded_ai(db_session)
    r = await ai.respond(
        history=[], user_text="Dr. Nonexistent qachon ishlaydi?", language="uz-UZ"
    )
    assert r.action is SafetyAction.TRANSFER


# === Language ================================================================
@pytest.mark.asyncio
async def test_russian_query_returns_russian_content(db_session: AsyncSession) -> None:
    ai = await _seeded_ai(db_session)
    r = await ai.respond(history=[], user_text="Сколько стоит консультация?", language="ru-RU")
    assert r.action is SafetyAction.ALLOW
    assert "150 000" in r.reply
    assert _CYRILLIC.search(r.reply)


@pytest.mark.asyncio
async def test_uzbek_query_returns_uzbek_content(db_session: AsyncSession) -> None:
    ai = await _seeded_ai(db_session)
    r = await ai.respond(history=[], user_text="Konsultatsiya narxi qancha?", language="uz-UZ")
    assert "so'm" in r.reply
    assert not _CYRILLIC.search(r.reply)


@pytest.mark.asyncio
async def test_answer_includes_source_metadata(db_session: AsyncSession) -> None:
    ai = await _seeded_ai(db_session)
    r = await ai.respond(history=[], user_text="Klinika manzili qayerda?", language="uz-UZ")
    assert r.sources
    assert "id" in r.sources[0] and "title" in r.sources[0]


# === Search service + CRUD ===================================================
@pytest.mark.asyncio
async def test_inactive_item_not_used(db_session: AsyncSession) -> None:
    kb = KnowledgeBaseService(db_session)
    await kb.create(
        category=KBCategory.SERVICES_PRICES.value,
        title="Maxfiy xizmat",
        content_uz="Maxfiy xizmat narxi: 999 so'm.",
        content_ru="Цена секретной услуги: 999 сум.",
        tags=["maxfiyxizmat"],
        is_active=False,
    )
    results = await kb.search("maxfiyxizmat narxi", "uz-UZ", intent=KBIntent.PRICE)
    assert results == []


@pytest.mark.asyncio
async def test_active_item_is_found(db_session: AsyncSession) -> None:
    kb = KnowledgeBaseService(db_session)
    await kb.create(
        category=KBCategory.SERVICES_PRICES.value,
        title="Maxsus xizmat",
        content_uz="Maxsus xizmat narxi: 50 000 so'm.",
        content_ru="Цена особой услуги: 50 000 сум.",
        tags=["maxsusxizmat", "narx"],
        is_active=True,
    )
    results = await kb.search("maxsusxizmat narxi", "uz-UZ", intent=KBIntent.PRICE)
    assert len(results) == 1
    assert "50 000" in results[0].content


@pytest.mark.asyncio
async def test_crud_lifecycle(db_session: AsyncSession) -> None:
    kb = KnowledgeBaseService(db_session)
    item = await kb.create(
        category=KBCategory.FAQ.value,
        title="Test",
        content_uz="uz",
        content_ru="ru",
        tags=["t"],
    )
    assert (await kb.get(item.id)).title == "Test"

    await kb.update(item.id, title="Test2", is_active=False)
    assert (await kb.get(item.id)).title == "Test2"

    items = await kb.list(category=KBCategory.FAQ.value)
    assert any(i.id == item.id for i in items)

    assert await kb.delete(item.id) is True
    assert await kb.get(item.id) is None


@pytest.mark.asyncio
async def test_seed_is_idempotent(db_session: AsyncSession) -> None:
    first = await seed_demo_clinic(db_session)
    second = await seed_demo_clinic(db_session)
    assert first > 0
    assert second == 0
