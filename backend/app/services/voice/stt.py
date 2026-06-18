"""Speech-to-text provider abstraction + mock + real (OpenAI Whisper) adapter.

Provider-first: the voice pipeline depends only on STTProvider. The mock is the
default (tests/simulation, no external calls). The real adapter is opt-in via
STT_PROVIDER and lazy-imports the OpenAI SDK, so neither tests nor mock mode need
the SDK or a key.
"""
from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

_CYRILLIC = re.compile(r"[а-яё]", re.IGNORECASE)


@dataclass
class STTResult:
    text: str
    language: str  # locale, e.g. "uz-UZ" | "ru-RU"
    confidence: Optional[float] = None  # None when the provider does not return it
    duration_ms: Optional[int] = None
    provider_metadata: dict = field(default_factory=dict)


class STTProviderError(Exception):
    """STT failed (decode/network/API). Mapped to a safe operator transfer."""


class STTProviderTimeoutError(STTProviderError):
    """STT timed out."""


class STTProvider(ABC):
    @abstractmethod
    async def transcribe(
        self,
        audio: bytes,
        *,
        content_type: str = "application/octet-stream",
        language: Optional[str] = None,
        text_hint: Optional[str] = None,
    ) -> STTResult:
        raise NotImplementedError


def _detect_locale(text: str) -> str:
    return "ru-RU" if _CYRILLIC.search(text) else "uz-UZ"


def _normalize_language(raw: Optional[str], text: str) -> str:
    """Map a provider language label to our locale; fall back to script detection."""
    if raw:
        low = raw.lower()
        if low.startswith(("ru", "рус")):
            return "ru-RU"
        if low.startswith(("uz", "ўзб", "узб")):
            return "uz-UZ"
    return _detect_locale(text)


class MockSTTProvider(STTProvider):
    """Deterministic STT for tests/simulation.

    Resolution order for the transcript: explicit `text_hint` (used by the
    `text_override` local-testing path) > UTF-8 decode of the audio bytes (lets a
    client send text-as-bytes deterministically) > a generic fallback phrase.
    Supports Uzbek/Russian/mixed via simple script detection.
    """

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    async def transcribe(
        self,
        audio: bytes,
        *,
        content_type: str = "application/octet-stream",
        language: Optional[str] = None,
        text_hint: Optional[str] = None,
    ) -> STTResult:
        if text_hint is not None:
            text = text_hint
        elif audio:
            try:
                text = audio.decode("utf-8").strip()
            except UnicodeDecodeError:
                text = ""
        else:
            text = ""
        if not text:
            text = "Salom"  # deterministic non-empty fallback

        locale = language or _detect_locale(text)
        return STTResult(
            text=text,
            language=locale,
            confidence=0.95,
            duration_ms=max(1, len(text) * 60),
            provider_metadata={"provider": "mock"},
        )


class RealSTTProvider(STTProvider):
    """OpenAI Whisper adapter (opt-in via STT_PROVIDER=openai_whisper).

    Lazy-imports the OpenAI SDK and accepts an injectable client so tests never
    touch the network. Never logs raw audio or the API key; provider errors are
    sanitized to a type name only.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "whisper-1",
        timeout: float = 15.0,
        language_hint: Optional[str] = None,
        client=None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self.timeout = timeout
        self._language_hint = language_hint
        self._client = client  # injectable for tests

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI  # lazy; needs the `stt` extra installed

            self._client = AsyncOpenAI(api_key=self._api_key, timeout=self.timeout)
        return self._client

    async def transcribe(
        self,
        audio: bytes,
        *,
        content_type: str = "application/octet-stream",
        language: Optional[str] = None,
        text_hint: Optional[str] = None,
    ) -> STTResult:
        # Deterministic override path (debugging) bypasses the real API.
        if text_hint is not None:
            return STTResult(
                text=text_hint,
                language=language or _detect_locale(text_hint),
                confidence=None,
                provider_metadata={"provider": "openai_whisper", "mode": "text_override"},
            )

        client = self._get_client()
        lang = language or self._language_hint
        # OpenAI accepts a (filename, bytes, content_type) tuple as the file.
        file_tuple = ("audio", audio, content_type)
        kwargs = dict(model=self._model, file=file_tuple, response_format="verbose_json")
        if lang:
            kwargs["language"] = lang[:2]  # ISO-639-1 hint, e.g. "uz" / "ru"
        try:
            resp = await asyncio.wait_for(
                client.audio.transcriptions.create(**kwargs), timeout=self.timeout
            )
        except asyncio.TimeoutError as exc:
            raise STTProviderTimeoutError("STT provider timed out") from exc
        except Exception as exc:  # never leak payload/secret
            raise STTProviderError(f"STT provider error: {type(exc).__name__}") from exc

        text = (getattr(resp, "text", "") or "").strip()
        raw_lang = getattr(resp, "language", None)
        duration = getattr(resp, "duration", None)
        duration_ms = int(duration * 1000) if isinstance(duration, (int, float)) else None
        return STTResult(
            text=text,
            language=_normalize_language(raw_lang, text),
            confidence=None,  # Whisper does not return a calibrated confidence
            duration_ms=duration_ms,
            provider_metadata={
                "provider": "openai_whisper",
                "model": self._model,
                "language": raw_lang,
            },
        )
