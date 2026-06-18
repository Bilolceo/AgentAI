"""Language enum + detection (uz / ru / unknown).

Uzbek is written in Latin script in this project; Russian in Cyrillic. Detection
is script-based: dominant script wins, and `is_mixed` flags utterances that
contain a meaningful amount of both.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

_CYRILLIC = re.compile(r"[а-яё]", re.IGNORECASE)
_LATIN = re.compile(r"[a-z]", re.IGNORECASE)

_LOCALE = {"uz": "uz-UZ", "ru": "ru-RU"}


class Language(str, Enum):
    UZ = "uz"
    RU = "ru"
    UNKNOWN = "unknown"

    @property
    def locale(self) -> str:
        """Downstream pipeline locale (guard/AIService use startswith('ru'))."""
        return _LOCALE.get(self.value, "uz-UZ")

    @classmethod
    def from_code(cls, code: Optional[str]) -> Optional[Language]:
        """Parse 'uz' / 'ru' / 'uz-UZ' / 'ru-RU' → Language; None if not given."""
        if not code:
            return None
        c = code.lower()
        if c.startswith("uz"):
            return cls.UZ
        if c.startswith("ru"):
            return cls.RU
        return None


@dataclass(frozen=True)
class LanguageDetection:
    language: Language  # dominant language, or UNKNOWN
    is_mixed: bool


class LanguageDetectionService:
    """Stateless, deterministic script-based detector."""

    def detect(self, text: str) -> LanguageDetection:
        cyr = len(_CYRILLIC.findall(text))
        lat = len(_LATIN.findall(text))

        if cyr == 0 and lat == 0:
            return LanguageDetection(Language.UNKNOWN, is_mixed=False)

        is_mixed = cyr >= 2 and lat >= 2
        language = Language.UZ if lat >= cyr else Language.RU
        return LanguageDetection(language, is_mixed=is_mixed)
