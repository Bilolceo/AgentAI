"""Post-LLM output safety validation (defense-in-depth).

The pre-LLM `MedicalSafetyGuardService` gates user *input*. This second layer
inspects the AI's *generated output* before it is returned to the caller and
blocks it if it contains content the AI must never produce (TZ §5.1): a
diagnosis, medicine/dosage advice, a treatment plan, third-party patient data,
or negative comparison of other clinics/doctors — including cases where unsafe
content slipped past the input guard (paraphrase, prompt injection, model error).

Design:
  - `SafetyReviewer` is the interface. Today we use `MockSafetyReviewer`, which
    wraps the pure, deterministic `DeterministicSafetyValidator` (no network).
  - `LLMSafetyReviewer` is a placeholder for a future model-based reviewer; it is
    NOT used yet (no real external LLM call here).
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app.services.safety.guard import (
    EMERGENCY_MESSAGE_RU,
    EMERGENCY_MESSAGE_UZ,
    ReasonCode,
)

# Safe replacement shown to the user when the AI output is blocked.
OUTPUT_BLOCK_MESSAGE_UZ = (
    "Kechirasiz, men bu masalada aniq javob bera olmayman. Xavfsizlik uchun sizni "
    "shifokor-mutaxassis yoki operatorga ulayman."
)
OUTPUT_BLOCK_MESSAGE_RU = (
    "Извините, я не могу дать точный ответ по этому вопросу. В целях безопасности "
    "я соединю вас со специалистом или оператором."
)


@dataclass(frozen=True)
class SafetyReviewResult:
    is_safe: bool
    reason_code: ReasonCode
    safe_message_uz: Optional[str]
    safe_message_ru: Optional[str]
    is_emergency: bool = False

    def message_for(self, language: str) -> Optional[str]:
        return self.safe_message_ru if language.startswith("ru") else self.safe_message_uz


_SAFE = SafetyReviewResult(True, ReasonCode.NONE, None, None)


def _blocked(reason: ReasonCode) -> SafetyReviewResult:
    return SafetyReviewResult(
        is_safe=False,
        reason_code=reason,
        safe_message_uz=OUTPUT_BLOCK_MESSAGE_UZ,
        safe_message_ru=OUTPUT_BLOCK_MESSAGE_RU,
    )


def _blocked_emergency() -> SafetyReviewResult:
    """AI mentioned an emergency but failed to direct to 103 → official message."""
    return SafetyReviewResult(
        is_safe=False,
        reason_code=ReasonCode.EMERGENCY,
        safe_message_uz=EMERGENCY_MESSAGE_UZ,
        safe_message_ru=EMERGENCY_MESSAGE_RU,
        is_emergency=True,
    )


class SafetyReviewer(ABC):
    """Interface for an output safety reviewer."""

    @abstractmethod
    async def review(self, text: str, language: str = "uz-UZ") -> SafetyReviewResult:
        raise NotImplementedError


# --- Output-side detection (assertion/advice oriented, not question oriented) --

_MED_TERMS = [
    "dori", "tabletka", "antibiotik", "ukol", "kapsula", "surtma", "kapla",
    "лекарств", "таблетк", "антибиотик", "укол", "мазь", "капл",
]
_MED_ADVICE_VERBS = [
    "iching", "ichib", "qabul qiling", "qabul qil", "tavsiya qila", "ichish kerak",
    "принимайте", "принимать", "выпейте", "пейте", "назначаю", "рекоменд",
]

_DISEASE_TERMS = [
    "gripp", "angina", "allergiya", "bronxit", "gastrit", "infeksiya", "virusli",
    "yallig'lan", "грипп", "ангина", "аллергия", "бронхит", "гастрит", "инфекц",
    "вирус", "воспален",
]

_TREATMENT_MARKERS = [
    "davola", "muolaja", "kompres", "bug'lan", "chayqang", "issiq suv bilan",
    "лечите", "лечение:", "компресс", "промывайте", "полоскайте", "прогревайте",
]

_DATA_DISCLOSURE_MARKERS = [
    "tahlil natijasi:", "bemorning natija", "natijasi:", "kasallik tarixi:",
    "результат анализ", "анализ пациент", "история болезни", "диагноз пациент",
]

_NEGATIVE_TALK_MARKERS = [
    "yomonroq", "ulardan yaxshi", "u klinika yomon", "boshqa klinika yomon",
    "shifokori yomon", "хуже", "плохая клиник", "плохой врач", "лучше чем у них",
]

# Emergency *situation* mentioned in the AI output (condition/symptom, not remedy).
_EMERGENCY_CONTEXT_TERMS = [
    # uz
    "yurak xuruji", "yurak tutib", "infarkt", "insult", "qon ketyap", "qon ketish",
    "nafas ololmas", "nafas qiyin", "hushini yo'qot", "behush", "favqulodda",
    "shoshilinch", "o'tkir holat", "zaharlanish", "talvasa", "qon yo'qot",
    # ru
    "инфаркт", "сердечный приступ", "инсульт", "кровотеч", "не может дышать",
    "трудно дышать", "теряет сознание", "без сознания", "неотложн",
    "острое состояние", "отравление", "судорог", "приступ",
]
# A clear directive to call 103 / go to a hospital / call an ambulance.
_EMERGENCY_DIRECTIVE_TERMS = [
    "103", "shifoxona", "kasalxona", "tez yordam", "shifoxonaga murojaat",
    "скор", "больниц", "стационар", "неотложку",
]


def _is_unsafe_emergency_handling(norm: str) -> bool:
    """Emergency situation mentioned but NOT directed to 103 / hospital."""
    has_context = _any(norm, _EMERGENCY_CONTEXT_TERMS)
    has_directive = _any(norm, _EMERGENCY_DIRECTIVE_TERMS)
    return has_context and not has_directive

# Dosage: digit-based and a few common word-number forms.
_DOSAGE_REGEXES = [
    re.compile(r"kuniga\s+\d+"),
    re.compile(r"\d+\s*mahal"),
    re.compile(r"\d+\s*tabletka"),
    re.compile(r"har\s+\d+\s*soat"),
    re.compile(r"\d+\s*mg"),
    re.compile(r"\d+\s*раз"),
    re.compile(r"по\s*\d+\s*таблет"),
    re.compile(r"каждые\s+\d+\s*час"),
    re.compile(r"\d+\s*мг"),
]
_DOSAGE_WORDS = [
    "kuniga uch mahal", "kuniga ikki mahal", "kuniga to'rt mahal",
    "три раза в день", "два раза в день", "по таблетке",
]


def _normalize(text: str) -> str:
    text = text.lower()
    for ch in ("ʻ", "`", "'", "ʼ", "’"):
        text = text.replace(ch, "'")
    return re.sub(r"\s+", " ", text).strip()


def _any(text: str, terms: list[str]) -> bool:
    return any(t in text for t in terms)


class DeterministicSafetyValidator:
    """Pure output validator. Returns the first unsafe category found, else safe."""

    def validate(self, text: str, language: str = "uz-UZ") -> SafetyReviewResult:
        norm = _normalize(text)

        # Unsafe emergency handling: emergency mentioned without a 103/hospital
        # directive → replace with the official emergency message (TZ §5.2).
        if _is_unsafe_emergency_handling(norm):
            return _blocked_emergency()

        # Diagnosis assertion (AI naming a disease / giving a diagnosis).
        if "tashxis" in norm or "диагноз" in norm or (
            ("sizda" in norm or "у вас" in norm) and _any(norm, _DISEASE_TERMS)
        ):
            return _blocked(ReasonCode.DIAGNOSIS)

        # Medicine advice (drug term + advice verb).
        if _any(norm, _MED_TERMS) and _any(norm, _MED_ADVICE_VERBS):
            return _blocked(ReasonCode.MEDICINE)

        # Dosage instructions.
        if _any(norm, _DOSAGE_WORDS) or any(r.search(norm) for r in _DOSAGE_REGEXES):
            return _blocked(ReasonCode.DOSAGE)

        # Treatment plan / self-care instructions.
        if _any(norm, _TREATMENT_MARKERS):
            return _blocked(ReasonCode.TREATMENT)

        # Third-party / private patient data leaked in the response.
        if _any(norm, _DATA_DISCLOSURE_MARKERS):
            return _blocked(ReasonCode.DATA_DISCLOSURE)

        # Negative comparison of other clinics/doctors.
        if _any(norm, _NEGATIVE_TALK_MARKERS):
            return _blocked(ReasonCode.NEGATIVE_TALK)

        return _SAFE


class MockSafetyReviewer(SafetyReviewer):
    """Deterministic reviewer used now (no external LLM)."""

    def __init__(self) -> None:
        self._validator = DeterministicSafetyValidator()

    async def review(self, text: str, language: str = "uz-UZ") -> SafetyReviewResult:
        return self._validator.validate(text, language)


class LLMSafetyReviewer(SafetyReviewer):
    """Future: ask a model to judge the response. Not enabled yet."""

    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._api_key = api_key

    async def review(self, text: str, language: str = "uz-UZ") -> SafetyReviewResult:
        # TODO: call the LLM reviewer once the simulation is validated.
        raise NotImplementedError("LLMSafetyReviewer is not enabled yet — use MockSafetyReviewer")


# Process-wide default reviewer (stateless — safe to share).
default_reviewer: SafetyReviewer = MockSafetyReviewer()
