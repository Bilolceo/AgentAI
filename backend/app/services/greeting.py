"""GreetingService — safe clinic greeting (no medical advice).

Bilingual fallback is used when the caller's language is unknown.
"""
from __future__ import annotations

from app.services.language import Language

GREETING_UZ = (
    "Assalomu alaykum! Klinikamizga murojaat qilganingiz uchun rahmat. "
    "Sizga qanday yordam bera olaman?"
)
GREETING_RU = (
    "Здравствуйте! Спасибо за обращение в нашу клинику. Чем я могу вам помочь?"
)
GREETING_BILINGUAL = f"{GREETING_UZ}\n{GREETING_RU}"


class GreetingService:
    def greet(self, language: Language) -> str:
        if language is Language.RU:
            return GREETING_RU
        if language is Language.UZ:
            return GREETING_UZ
        return GREETING_BILINGUAL
