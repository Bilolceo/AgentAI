"""KnowledgeBaseService — CRUD + deterministic search (no embeddings).

Search strategy:
  - intent narrows the candidate categories;
  - if the query has *specific* tokens (a service/doctor name, not just generic
    question words) we require a token match → unknown items return nothing
    (so AIService transfers instead of inventing an answer);
  - otherwise (a generic question like "what are your hours") we return the
    category's items filtered by the intent's anchor tags.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_item import KnowledgeItem
from app.services.knowledge.intent import KBIntent


class KBCategory(str, Enum):
    CLINIC_INFO = "clinic_info"
    BRANCHES = "branches"
    SERVICES_PRICES = "services_prices"
    DOCTORS = "doctors"
    DOCTOR_SCHEDULE = "doctor_schedule"
    FAQ = "faq"
    PREPARATION_INSTRUCTIONS = "preparation_instructions"
    OPERATOR_RULES = "operator_rules"
    EMERGENCY_POLICY = "emergency_policy"


@dataclass(frozen=True)
class KBMatch:
    id: int
    title: str
    content: str  # in the requested language
    category: str


class KnowledgeSearch(Protocol):
    async def search(
        self, query: str, language: str, intent: Optional[KBIntent] = None
    ) -> list[KBMatch]: ...


# Generic question words / price words to drop so only distinctive tokens remain.
_STOPWORDS = {
    # uz
    "narx", "narxi", "narxlari", "qancha", "qanaqa", "qanday", "qachon", "pul",
    "soat", "nechada", "vaqt", "vaqti", "vaqtingiz", "ish", "jadval", "qabul",
    "manzil", "manzili", "manzilingiz", "qayer", "qayerda", "joylashgan", "borish",
    "klinika", "klinikangiz", "bor", "bormi", "qiling", "iltimos", "men", "sizning",
    "haqida", "kerak", "ber", "bering", "ishlaydi", "ishlaysiz", "ishlaydimi", "ishlay",
    # ru
    "цена", "цены", "стоимость", "сколько", "стоит", "часы", "работы", "график",
    "расписание", "время", "адрес", "где", "находитесь", "находится", "клиника",
    "какие", "как", "ваш", "ваша", "вы", "нужно", "пожалуйста", "прием", "приём",
    "работает", "работаете",
}

_INTENT_CATEGORIES: dict[KBIntent, list[KBCategory]] = {
    KBIntent.PRICE: [KBCategory.SERVICES_PRICES],
    KBIntent.SCHEDULE: [KBCategory.CLINIC_INFO, KBCategory.DOCTOR_SCHEDULE],
    KBIntent.ADDRESS: [KBCategory.CLINIC_INFO, KBCategory.BRANCHES],
    KBIntent.DOCTOR: [KBCategory.DOCTORS, KBCategory.DOCTOR_SCHEDULE],
    KBIntent.SERVICE: [KBCategory.SERVICES_PRICES],
    KBIntent.PREPARATION: [KBCategory.PREPARATION_INSTRUCTIONS],
    KBIntent.CLINIC_INFO: [KBCategory.CLINIC_INFO],
}

_INTENT_ANCHOR_TAGS: dict[KBIntent, set[str]] = {
    KBIntent.PRICE: {"narx", "price", "цена"},
    KBIntent.SCHEDULE: {"ish_vaqti", "hours", "часы"},
    KBIntent.ADDRESS: {"manzil", "address", "адрес"},
    KBIntent.DOCTOR: {"shifokor", "doctor", "врач"},
    KBIntent.SERVICE: {"xizmat", "service", "услуга"},
    KBIntent.PREPARATION: {"tayyorgarlik", "preparation", "подготовка"},
    KBIntent.CLINIC_INFO: {"klinika", "clinic"},
}


def _normalize(text: str) -> str:
    text = text.lower()
    for ch in ("ʻ", "`", "'", "ʼ", "’"):
        text = text.replace(ch, "'")
    return text


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zа-яё0-9']+", _normalize(text)) if len(t) >= 3]


def _searchable(item: KnowledgeItem) -> str:
    tags = " ".join(item.tags or [])
    return _normalize(f"{item.title} {item.content_uz} {item.content_ru} {tags}")


def _content(item: KnowledgeItem, language: str) -> str:
    return item.content_ru if language.startswith("ru") else item.content_uz


class KnowledgeBaseService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- CRUD ---------------------------------------------------------------
    async def create(
        self,
        *,
        category: str,
        title: str,
        content_uz: str,
        content_ru: str,
        tags: Optional[list[str]] = None,
        is_active: bool = True,
    ) -> KnowledgeItem:
        item = KnowledgeItem(
            category=category,
            title=title,
            content_uz=content_uz,
            content_ru=content_ru,
            tags=tags or [],
            is_active=is_active,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def get(self, item_id: int) -> Optional[KnowledgeItem]:
        return await self._session.get(KnowledgeItem, item_id)

    async def list(
        self, *, category: Optional[str] = None, active_only: bool = False
    ) -> list[KnowledgeItem]:
        stmt = select(KnowledgeItem)
        if category:
            stmt = stmt.where(KnowledgeItem.category == category)
        if active_only:
            stmt = stmt.where(KnowledgeItem.is_active.is_(True))
        return list((await self._session.execute(stmt.order_by(KnowledgeItem.id))).scalars())

    async def update(self, item_id: int, **fields) -> Optional[KnowledgeItem]:
        item = await self.get(item_id)
        if item is None:
            return None
        for key, value in fields.items():
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)
        await self._session.flush()
        return item

    async def delete(self, item_id: int) -> bool:
        item = await self.get(item_id)
        if item is None:
            return False
        await self._session.delete(item)
        await self._session.flush()
        return True

    # --- Search -------------------------------------------------------------
    async def search(
        self,
        query: str,
        language: str,
        intent: Optional[KBIntent] = None,
        *,
        top_k: int = 5,
    ) -> list[KBMatch]:
        categories = _INTENT_CATEGORIES.get(intent) if intent else None

        stmt = select(KnowledgeItem).where(KnowledgeItem.is_active.is_(True))
        if categories:
            stmt = stmt.where(KnowledgeItem.category.in_([c.value for c in categories]))
        items = list((await self._session.execute(stmt.order_by(KnowledgeItem.id))).scalars())
        if not items:
            return []

        specific = [t for t in _tokens(query) if t not in _STOPWORDS]

        if specific:
            scored: list[tuple[int, KnowledgeItem]] = []
            for item in items:
                text = _searchable(item)
                score = sum(1 for t in specific if t in text)
                if score > 0:
                    scored.append((score, item))
            scored.sort(key=lambda s: (-s[0], s[1].id))
            chosen = [item for _, item in scored[:top_k]]
        else:
            anchors = _INTENT_ANCHOR_TAGS.get(intent, set()) if intent else set()
            if anchors:
                chosen = [
                    it for it in items
                    if anchors & {t.lower() for t in (it.tags or [])}
                ][:top_k]
            else:
                chosen = items[:top_k]

        return [
            KBMatch(id=it.id, title=it.title, content=_content(it, language), category=it.category)
            for it in chosen
        ]
