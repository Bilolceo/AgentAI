"""KB intent classification (deterministic keyword-based).

Decides what kind of clinic fact the caller is asking for, so the KB search can
target the right categories and AIService can refuse to hallucinate missing facts.
"""
from __future__ import annotations

import re
from enum import Enum


class KBIntent(str, Enum):
    PRICE = "price"
    SCHEDULE = "schedule"
    ADDRESS = "address"
    DOCTOR = "doctor"
    SERVICE = "service"
    PREPARATION = "preparation"
    CLINIC_INFO = "clinic_info"
    GENERAL = "general"


# Intents that MUST be grounded in the KB; if the KB has nothing, transfer to a
# human instead of letting the model invent an answer (TZ §4.2 / §5).
FACTUAL_INTENTS = {
    KBIntent.PRICE,
    KBIntent.SCHEDULE,
    KBIntent.ADDRESS,
    KBIntent.DOCTOR,
    KBIntent.SERVICE,
    KBIntent.PREPARATION,
    KBIntent.CLINIC_INFO,
}

# Checked in order — schedule before price so "qabul vaqti qancha" is schedule.
_INTENT_KEYWORDS: list[tuple[KBIntent, list[str]]] = [
    (KBIntent.ADDRESS, ["manzil", "qayer", "qanday borish", "адрес", "где наход", "где вы", "как добрат"]),
    (KBIntent.SCHEDULE, ["ish vaqt", "soat nec", "qachon", "jadval", "qabul vaqt", "ochiq",
                         "часы работ", "график", "расписан", "во сколько", "когда работа", "время приём"]),
    (KBIntent.PRICE, ["narx", "qancha", "necha pul", "pul", "цена", "сколько стоит", "стоит", "стоимость"]),
    (KBIntent.PREPARATION, ["tayyorgarlik", "tayyorlan", "подготов"]),
    (KBIntent.DOCTOR, ["shifokor", "doktor", "врач", "доктор", "mutaxassis", "специалист"]),
    (KBIntent.SERVICE, ["xizmat", "услуг"]),
    (KBIntent.CLINIC_INFO, ["klinika haqida", "о клинике", "kontakt", "telefon", "телефон"]),
]


def _normalize(text: str) -> str:
    text = text.lower()
    for ch in ("ʻ", "`", "'", "ʼ", "’"):
        text = text.replace(ch, "'")
    return re.sub(r"\s+", " ", text).strip()


def classify_intent(text: str) -> KBIntent:
    norm = _normalize(text)
    for intent, keywords in _INTENT_KEYWORDS:
        if any(kw in norm for kw in keywords):
            return intent
    return KBIntent.GENERAL
