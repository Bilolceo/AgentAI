"""MedicalSafetyGuardService — medical-safety + escalation guardrails (TZ §5, §4.6).

Pure, dependency-free logic so it is fully unit-testable without DB/network/LLM.
It classifies a user utterance BEFORE the LLM is called and decides whether the
AI may answer, must return a safe canned reply, must hand off to a human
operator, or must give emergency guidance.

Hard rules (TZ §5.1 — MUST NOT be weakened or bypassed):
  - no diagnosis, disease guessing, medicine, dosage, or treatment plan
  - no disclosing personal/medical data to third parties
  - no negative talk about other clinics/doctors
  - do not keep talking during an emergency (stop the flow, give 103 guidance)

Escalation triggers (TZ §4.6): explicit operator request, complaint, aggressive
tone, unclear price/schedule, and (post-generation) low AI confidence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# --- Verbatim emergency message (TZ §5.2) -----------------------------------
EMERGENCY_MESSAGE_UZ = (
    "Bu holat shoshilinch tibbiy yordam talab qilishi mumkin. Iltimos, darhol 103 "
    "raqamiga qo'ng'iroq qiling yoki eng yaqin shifoxonaga murojaat qiling."
)
EMERGENCY_MESSAGE_RU = (
    "Это состояние может требовать неотложной медицинской помощи. Пожалуйста, "
    "немедленно позвоните по номеру 103 или обратитесь в ближайшую больницу."
)

# --- Safe canned replies per reason (no LLM is called when these fire) -------
_DEFLECT_MEDICAL_UZ = (
    "Kechirasiz, men tashxis qo'ya olmayman yoki dori tavsiya eta olmayman. "
    "Sizni shifokor-mutaxassisga yoki operatorga ulayman."
)
_DEFLECT_MEDICAL_RU = (
    "Извините, я не могу ставить диагноз или назначать лекарства. "
    "Я соединю вас со специалистом или оператором."
)
_DATA_DISCLOSURE_UZ = (
    "Kechirasiz, men shaxsiy tibbiy ma'lumotlarni telefon orqali boshqa shaxsga "
    "bera olmayman. Shaxsni tasdiqlash uchun sizni operatorga ulayman."
)
_DATA_DISCLOSURE_RU = (
    "Извините, я не могу передавать личные медицинские данные по телефону третьим "
    "лицам. Для подтверждения личности я соединю вас с оператором."
)
_NEGATIVE_TALK_UZ = (
    "Kechirasiz, men boshqa klinika yoki shifokorlar haqida fikr bildira olmayman. "
    "Lekin bizning klinikamiz bo'yicha yordam bera olaman."
)
_NEGATIVE_TALK_RU = (
    "Извините, я не могу комментировать другие клиники или врачей. Но я могу помочь "
    "по нашей клинике."
)
_OPERATOR_UZ = "Albatta, sizni hoziroq operatorga ulayman."
_OPERATOR_RU = "Конечно, сейчас я соединю вас с оператором."
_COMPLAINT_UZ = (
    "Noqulaylik uchun uzr so'rayman. Masalangizni hal qilish uchun sizni operatorga ulayman."
)
_COMPLAINT_RU = (
    "Приношу извинения за неудобства. Чтобы решить ваш вопрос, я соединю вас с оператором."
)
_ANGRY_UZ = "Sizni tushunaman. Yaxshisi, sizni jonli operatorga ulay."
_ANGRY_RU = "Я вас понимаю. Давайте я соединю вас с живым оператором."
_PRICE_UNCLEAR_UZ = (
    "Aniq narx yoki bo'sh vaqtni operator tasdiqlab beradi. Sizni operatorga ulayman."
)
_PRICE_UNCLEAR_RU = (
    "Точную цену или свободное время подтвердит оператор. Я соединю вас с оператором."
)
_LOW_CONFIDENCE_UZ = (
    "Bu savolga aniq javob bera olmasligim mumkin. Aniqlik uchun sizni operatorga ulayman."
)
_LOW_CONFIDENCE_RU = (
    "Возможно, я не смогу ответить точно. Для уверенности я соединю вас с оператором."
)


class SafetyAction(str, Enum):
    ALLOW = "allow"            # safe — proceed to the AI provider
    SAFE_REPLY = "safe_reply"  # return canned safe reply, no LLM, no transfer
    TRANSFER = "transfer"      # hand off to a human operator
    EMERGENCY = "emergency"    # urgent symptoms — emergency guidance + stop flow


class ReasonCode(str, Enum):
    NONE = "none"
    EMERGENCY = "emergency"
    DIAGNOSIS = "diagnosis_request"
    MEDICINE = "medicine_request"
    DOSAGE = "dosage_request"
    TREATMENT = "treatment_request"
    DATA_DISCLOSURE = "data_disclosure_request"
    NEGATIVE_TALK = "negative_competitor_talk"
    OPERATOR_REQUEST = "operator_request"
    COMPLAINT = "complaint"
    ANGRY = "angry_user"
    PRICE_OR_SCHEDULE_UNCLEAR = "price_or_schedule_unclear"
    LOW_CONFIDENCE = "low_ai_confidence"
    UNSAFE_OUTPUT = "unsafe_ai_output"  # post-LLM validator blocked the response


# Backward-compatible alias (older imports used `SafetyCategory`).
SafetyCategory = ReasonCode

# Confidence below this → transfer to operator (TZ §4.6 "low confidence").
CONFIDENCE_THRESHOLD = 0.55


@dataclass(frozen=True)
class SafetyDecision:
    action: SafetyAction
    reason_code: ReasonCode
    safe_message_uz: Optional[str]
    safe_message_ru: Optional[str]
    should_transfer_operator: bool
    is_emergency: bool

    def message_for(self, language: str) -> Optional[str]:
        return self.safe_message_ru if language.startswith("ru") else self.safe_message_uz

    # Backward-compat for older callers.
    @property
    def category(self) -> ReasonCode:
        return self.reason_code

    @property
    def response(self) -> Optional[str]:  # uz default, like the old field
        return self.safe_message_uz


def _decision(
    action: SafetyAction, reason: ReasonCode, uz: Optional[str], ru: Optional[str]
) -> SafetyDecision:
    return SafetyDecision(
        action=action,
        reason_code=reason,
        safe_message_uz=uz,
        safe_message_ru=ru,
        should_transfer_operator=action in (SafetyAction.TRANSFER, SafetyAction.EMERGENCY),
        is_emergency=action is SafetyAction.EMERGENCY,
    )


_ALLOW = _decision(SafetyAction.ALLOW, ReasonCode.NONE, None, None)


# --- Keyword tables (lower-cased substring match; uz stems kept short). -------
# uz lists include Latin apostrophe-normalized stems; ru lists Cyrillic.

_EMERGENCY_KEYWORDS = [
    # uz
    "nafas ol", "nafas qiyin", "nafas yet", "bo'g'il", "bugil", "hushidan ket",
    "behush", "ko'krak og'ri", "kokrak ogri", "yurak tutib", "yurak sanch",
    "infarkt", "insult", "qon ket", "qattiq qon", "ko'p qon", "zaharlan",
    "es-hushini yo'qot", "talvasa", "o'lib qol", "olib qol", "tomir kesil",
    "kuyib qol", "behol yiqil",
    # ru
    "не могу дышать", "задыхаюсь", "трудно дышать", "потерял сознание",
    "без сознания", "теряю сознание", "боль в груди", "инфаркт", "инсульт",
    "кровотечение", "сильное кровотеч", "отравлен", "судорог", "приступ",
]

_DIAGNOSIS_KEYWORDS = [
    # uz
    "tashxis", "tashhis", "qanday kasallik", "qaysi kasallik", "menda nima",
    "nima kasallik", "kasalligim nima", "nima bo'ldi menga", "kasalmanmi",
    # ru
    "диагноз", "поставьте диагноз", "что у меня за болезн", "какая у меня болезн",
    "чем я болен", "что со мной", "это что за болезнь",
]

_MEDICINE_KEYWORDS = [
    # uz
    "qanday dori", "qaysi dori", "dori bering", "qanaqa dori", "dori tavsiya",
    "dori ayting", "qanday tabletka", "qaysi tabletka", "qanaqa tabletka",
    "antibiotik ich", "qanday ukol", "qaysi ukol",
    # ru
    "какое лекарство", "какую таблетку", "какие таблетки", "посоветуйте лекарств",
    "назначьте лекарств", "какой антибиотик", "какой укол", "что выпить от",
    "что принять от",
]

_DOSAGE_KEYWORDS = [
    # uz
    "qancha ich", "necha mahal ich", "necha marta ich", "necha kun ich", "doza",
    "qancha mg", "qancha gramm ich",
    # ru
    "какая дозировк", "сколько раз принимать", "сколько пить", "сколько дней пить",
    "какая доза", "сколько миллиграмм", "по сколько таблеток",
]

_TREATMENT_KEYWORDS = [
    # uz
    "qanday davola", "qanday davolan", "uyda davola", "davolash usul",
    "o'zimni davola", "qanday tuzal", "qanday sog'ay",
    # ru
    "как лечить", "как лечиться", "лечение дома", "как вылечить", "схему лечения",
    "как избавиться от болезни", "чем лечить",
]

# Advice categories (order preserved). Must run right after emergency.
_ADVICE_TABLE: list[tuple[ReasonCode, list[str]]] = [
    (ReasonCode.DIAGNOSIS, _DIAGNOSIS_KEYWORDS),
    (ReasonCode.MEDICINE, _MEDICINE_KEYWORDS),
    (ReasonCode.DOSAGE, _DOSAGE_KEYWORDS),
    (ReasonCode.TREATMENT, _TREATMENT_KEYWORDS),
]

# Third-party medical-data disclosure (compound: third-party term + data term).
_THIRD_PARTY_TERMS = [
    "boshqa odam", "boshqa bemor", "boshqa kishi", "qarindosh", "qo'shni",
    "do'stim", "tanishim", "erim", "xotinim", "akam", "ukam", "onam", "otam",
    "buvim", "bobom", "farzand", "bolam", "singlim", "opam", "kimningdir",
    # ru
    "другого пациент", "другого человек", "мужа", "жены", "брата", "сестры",
    "родственник", "соседа", "друга", "сына", "дочери", "чужой", "чужие",
    "кого-то",
]
_MED_DATA_TERMS = [
    "tahlil natija", "natijasini ayt", "natijalarini ayt", "kasallik tarixi",
    "tibbiy ma'lumot", "tibbiy karta", "analiz natija",
    # ru
    "результат анализ", "результаты анализ", "историю болезни", "история болезни",
    "медицинские данные", "медкарт", "карту пациент",
]
_DATA_DISCLOSURE_EXPLICIT = [
    "boshqa odamning tahlili", "boshqa bemorning natija", "данные пациента",
    "чужие анализы", "чужой анализ", "историю болезни другого",
]

# Negative talk about other clinics/doctors.
_NEGATIVE_TALK_KEYWORDS = [
    # uz
    "boshqa klinika yomon", "falon klinika yomon", "u klinika yomon",
    "boshqa shifokor yomon", "u shifokor yomon", "qaysi klinika yomon",
    "qaysi shifokor yomon", "ular yaxshimi yo'qmi", "ulardan yaxshimisiz",
    "boshqa klinikani yomonla", "shifokorni yomonla",
    # ru
    "другая клиника плохая", "та клиника плохая", "этот врач плохой",
    "тот врач плохой", "какая клиника плохая", "какой врач плохой",
    "вы лучше чем", "они хуже", "плохо отзовитесь",
]

# Explicit operator request.
_OPERATOR_REQUEST_KEYWORDS = [
    # uz
    "operatorga ulang", "operatorga ula", "operator kerak", "operator bilan",
    "jonli operator", "tirik odam bilan", "tirik operator", "menejer bilan",
    "inson bilan gaplash", "odam bilan gaplash", "real operator",
    # ru
    "оператор нужен", "позовите оператор", "переключите на оператор",
    "соедините с оператор", "живой оператор", "живого человека", "живого оператор",
    "дайте человека", "с человеком поговорить", "менеджер",
]

# Complaint / dissatisfaction.
_COMPLAINT_KEYWORDS = [
    # uz
    "shikoyat", "norozi", "shikoyat qil", "sifatsiz xizmat", "yomon xizmat",
    "pul qaytar", "pulimni qaytar", "aldadingiz", "aldashdi", "haq to'la",
    "javob berishmadi", "kutdim javob yo'q",
    # ru
    "жалоба", "хочу пожаловаться", "недоволен", "недовольна", "верните деньги",
    "обманули", "плохое обслуживание", "некачественн", "претензия",
]

# Aggressive / angry tone (keywords; also see _looks_aggressive heuristic).
_ANGRY_KEYWORDS = [
    # uz
    "jahlim chiqdi", "asabim buzildi", "bezor qildingiz", "bezor bo'ldim",
    "ahmoq", "jinni", "safsata", "uyat", "yetar endi", "bo'ldi qil",
    # ru
    "вы издеваетесь", "издевательство", "безобразие", "отвратительно", "идиот",
    "хватит уже", "достали", "бесите", "вы что издева", "это возмутительно",
]

# Price / schedule that the AI must NOT guess (TZ §4.2) — narrow to genuine
# uncertainty / negotiation / availability so plain "narx qancha?" stays ALLOW.
_PRICE_SCHEDULE_UNCLEAR_KEYWORDS = [
    # uz — price uncertainty / negotiation
    "chegirma bormi", "aksiya bormi", "sug'urta", "sugurta", "narx o'zgar",
    "aniq narx", "kafolatlangan narx", "eng arzon", "bo'lib to'la", "kreditga",
    "narxi tushadimi", "chegirma qil",
    # uz — schedule / availability that needs real data
    "qaysi kun bo'sh", "qachon bo'sh", "bo'sh joy bormi", "navbatsiz",
    "shoshilinch yozil", "bugun yozilsam bo'lad",
    # ru — price
    "есть скидка", "акция есть", "страховк", "цена изменилась", "точная цена",
    "гарантированная цена", "самое дешёвое", "в рассрочку", "в кредит",
    "цена снизит",
    # ru — schedule
    "когда есть свободн", "есть свободное время", "есть запись на сегодня",
    "без очереди", "срочно записаться",
]


def _normalize(text: str) -> str:
    text = text.lower()
    # Normalize Uzbek apostrophe variants (oʻ / o' / o` / oʼ).
    for ch in ("ʻ", "`", "'", "ʼ", "’"):
        text = text.replace(ch, "'")
    return re.sub(r"\s+", " ", text).strip()


def _matches(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)


def _is_data_disclosure(norm: str) -> bool:
    if _matches(norm, _DATA_DISCLOSURE_EXPLICIT):
        return True
    return _matches(norm, _THIRD_PARTY_TERMS) and _matches(norm, _MED_DATA_TERMS)


def _looks_aggressive(original: str) -> bool:
    """Heuristic for shouting/aggression independent of keyword lists."""
    letters = [c for c in original if c.isalpha()]
    if len(letters) >= 5:
        caps = sum(1 for c in letters if c.isupper())
        if caps / len(letters) > 0.7:
            return True
    # Repeated shouting punctuation, but only on a non-trivial utterance.
    return original.count("!") >= 3 and len(letters) >= 8


class MedicalSafetyGuardService:
    """Decides the safety action for a user utterance. Stateless and pure."""

    def evaluate(self, text: str, language: str = "uz-UZ") -> SafetyDecision:
        norm = _normalize(text)

        # 1) Emergency — highest priority, stop the flow.
        if _matches(norm, _EMERGENCY_KEYWORDS):
            return _decision(
                SafetyAction.EMERGENCY, ReasonCode.EMERGENCY,
                EMERGENCY_MESSAGE_UZ, EMERGENCY_MESSAGE_RU,
            )

        # 2) Medical advice (diagnosis / medicine / dosage / treatment) — never weaken.
        for reason, keywords in _ADVICE_TABLE:
            if _matches(norm, keywords):
                return _decision(
                    SafetyAction.TRANSFER, reason,
                    _DEFLECT_MEDICAL_UZ, _DEFLECT_MEDICAL_RU,
                )

        # 3) Third-party medical-data disclosure (TZ §5.1).
        if _is_data_disclosure(norm):
            return _decision(
                SafetyAction.TRANSFER, ReasonCode.DATA_DISCLOSURE,
                _DATA_DISCLOSURE_UZ, _DATA_DISCLOSURE_RU,
            )

        # 4) Explicit operator request (TZ §4.6).
        if _matches(norm, _OPERATOR_REQUEST_KEYWORDS):
            return _decision(
                SafetyAction.TRANSFER, ReasonCode.OPERATOR_REQUEST,
                _OPERATOR_UZ, _OPERATOR_RU,
            )

        # 5) Complaint.
        if _matches(norm, _COMPLAINT_KEYWORDS):
            return _decision(
                SafetyAction.TRANSFER, ReasonCode.COMPLAINT,
                _COMPLAINT_UZ, _COMPLAINT_RU,
            )

        # 6) Aggressive / angry tone.
        if _matches(norm, _ANGRY_KEYWORDS) or _looks_aggressive(text):
            return _decision(
                SafetyAction.TRANSFER, ReasonCode.ANGRY, _ANGRY_UZ, _ANGRY_RU
            )

        # 7) Unclear price / schedule (TZ §4.2).
        if _matches(norm, _PRICE_SCHEDULE_UNCLEAR_KEYWORDS):
            return _decision(
                SafetyAction.TRANSFER, ReasonCode.PRICE_OR_SCHEDULE_UNCLEAR,
                _PRICE_UNCLEAR_UZ, _PRICE_UNCLEAR_RU,
            )

        # 8) Negative talk about other clinics/doctors — safe decline, no transfer.
        if _matches(norm, _NEGATIVE_TALK_KEYWORDS):
            return _decision(
                SafetyAction.SAFE_REPLY, ReasonCode.NEGATIVE_TALK,
                _NEGATIVE_TALK_UZ, _NEGATIVE_TALK_RU,
            )

        # 9) Otherwise allow the LLM to answer.
        return _ALLOW

    def evaluate_confidence(
        self, confidence: Optional[float], language: str = "uz-UZ"
    ) -> SafetyDecision:
        """Post-generation: transfer if the AI's confidence is below threshold.

        `confidence` is None when the provider does not report it → ALLOW.
        """
        if confidence is not None and confidence < CONFIDENCE_THRESHOLD:
            return _decision(
                SafetyAction.TRANSFER, ReasonCode.LOW_CONFIDENCE,
                _LOW_CONFIDENCE_UZ, _LOW_CONFIDENCE_RU,
            )
        return _ALLOW


# Backward-compatible alias + process-wide singleton (stateless — safe to share).
SafetyGuardService = MedicalSafetyGuardService
safety_guard = MedicalSafetyGuardService()
