"""Text-to-speech provider abstraction + deterministic mock + real adapter.

Provider-first: the voice pipeline depends only on TTSProvider. The mock returns
deterministic fake audio bytes (no synthesis, no external calls) and stays the
default. The real adapter (OpenAI TTS) is opt-in via TTS_PROVIDER and lazy-imports
the OpenAI SDK, so neither tests nor mock mode need the SDK or a key.
"""
from __future__ import annotations

import asyncio
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

# Configured output format -> response content type. Only these formats are
# supported; the provider emits exactly the one it is configured with.
TTS_FORMAT_CONTENT_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "opus": "audio/opus",
    "aac": "audio/aac",
    "flac": "audio/flac",
    "pcm": "audio/pcm",
}


@dataclass
class TTSResult:
    text: str
    language: str  # locale
    voice: str
    audio_bytes: Optional[bytes] = None
    audio_url: Optional[str] = None
    content_type: str = "audio/mpeg"
    duration_ms: Optional[int] = None
    provider_metadata: dict = field(default_factory=dict)


class TTSProviderError(Exception):
    """TTS failed (synthesis/network/API/too-long). Mapped to a safe transfer."""


class TTSProviderTimeoutError(TTSProviderError):
    """TTS timed out."""


def _resolve_voice(language: str, voice: Optional[str], voice_uz: str, voice_ru: str) -> str:
    """Deterministic voice selection: explicit override > language locale."""
    if voice:
        return voice
    return voice_ru if language.startswith("ru") else voice_uz


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(
        self, text: str, *, language: str, voice: Optional[str] = None
    ) -> TTSResult:
        raise NotImplementedError


class MockTTSProvider(TTSProvider):
    """Deterministic fake-audio TTS for tests/simulation."""

    def __init__(
        self,
        voice_uz: str = "uz-UZ-MadinaNeural",
        voice_ru: str = "ru-RU-SvetlanaNeural",
        timeout: float = 15.0,
    ) -> None:
        self._voice_uz = voice_uz
        self._voice_ru = voice_ru
        self.timeout = timeout

    async def synthesize(
        self, text: str, *, language: str, voice: Optional[str] = None
    ) -> TTSResult:
        resolved = _resolve_voice(language, voice, self._voice_uz, self._voice_ru)
        # Deterministic fake audio: a marker plus the UTF-8 text. No real audio.
        audio = b"MOCK-AUDIO:" + text.encode("utf-8")
        return TTSResult(
            text=text,
            language=language,
            voice=resolved,
            audio_bytes=audio,
            audio_url=None,
            content_type="audio/mpeg",
            duration_ms=max(1, len(text) * 60),
            provider_metadata={"provider": "mock"},
        )


async def _read_audio_bytes(resp) -> bytes:
    """Extract audio bytes from an OpenAI binary speech response.

    The SDK has used both a `.content` attribute and a `.read()` method across
    versions; support both (and an async `read`) without leaking the payload.
    """
    data = getattr(resp, "content", None)
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    reader = getattr(resp, "read", None)
    if callable(reader):
        out = reader()
        if inspect.isawaitable(out):
            out = await out
        if isinstance(out, (bytes, bytearray)):
            return bytes(out)
    raise TTSProviderError("TTS provider returned no audio")


class RealTTSProvider(TTSProvider):
    """OpenAI TTS adapter (opt-in via TTS_PROVIDER=openai_tts).

    Lazy-imports the OpenAI SDK and accepts an injectable client so tests never
    touch the network. Never logs raw audio or the API key; provider errors are
    sanitized to a type name only. Text above `max_text_chars` is rejected as a
    provider error so the pipeline degrades to a safe operator transfer.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "tts-1",
        voice_uz: str = "alloy",
        voice_ru: str = "nova",
        audio_format: str = "mp3",
        timeout: float = 15.0,
        max_text_chars: int = 4000,
        client=None,
    ) -> None:
        if audio_format not in TTS_FORMAT_CONTENT_TYPES:
            raise ValueError(f"Unsupported TTS audio_format: {audio_format}")
        self._api_key = api_key
        self._model = model
        self._voice_uz = voice_uz
        self._voice_ru = voice_ru
        self._audio_format = audio_format
        self.timeout = timeout
        self._max_text_chars = max_text_chars
        self._client = client  # injectable for tests

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI  # lazy; needs the `tts` extra installed

            self._client = AsyncOpenAI(api_key=self._api_key, timeout=self.timeout)
        return self._client

    async def synthesize(
        self, text: str, *, language: str, voice: Optional[str] = None
    ) -> TTSResult:
        if len(text) > self._max_text_chars:
            # Too long to synthesize safely -> degrade to operator transfer.
            raise TTSProviderError(
                f"TTS text exceeds max_text_chars ({self._max_text_chars})"
            )
        resolved = _resolve_voice(language, voice, self._voice_uz, self._voice_ru)
        client = self._get_client()
        try:
            resp = await asyncio.wait_for(
                client.audio.speech.create(
                    model=self._model,
                    voice=resolved,
                    input=text,
                    response_format=self._audio_format,
                ),
                timeout=self.timeout,
            )
            audio_bytes = await _read_audio_bytes(resp)
        except asyncio.TimeoutError as exc:
            raise TTSProviderTimeoutError("TTS provider timed out") from exc
        except TTSProviderError:
            raise  # already sanitized (no audio / too long)
        except Exception as exc:  # never leak payload/secret
            raise TTSProviderError(f"TTS provider error: {type(exc).__name__}") from exc

        return TTSResult(
            text=text,
            language=language,
            voice=resolved,
            audio_bytes=audio_bytes,
            audio_url=None,
            content_type=TTS_FORMAT_CONTENT_TYPES[self._audio_format],
            duration_ms=None,  # OpenAI TTS does not return a duration
            provider_metadata={
                "provider": "openai_tts",
                "model": self._model,
                "format": self._audio_format,
            },
        )
