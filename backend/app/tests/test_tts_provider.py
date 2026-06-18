"""Real TTS (OpenAI) adapter + provider selection (fake client only).

No real key, no network: a fake OpenAI client is injected.
"""
from __future__ import annotations

import asyncio

import pytest

from app.api.deps import get_tts_provider
from app.core.config import settings
from app.services.voice.tts import (
    MockTTSProvider,
    RealTTSProvider,
    TTSProviderError,
    TTSProviderTimeoutError,
    TTSResult,
)


# --- fake OpenAI client -----------------------------------------------------
class _Binary:
    def __init__(self, content: bytes) -> None:
        self.content = content


class _Speech:
    def __init__(self, content=b"ID3-FAKE-MP3", exc=None, sleep=0.0):
        self._content, self._exc, self._sleep = content, exc, sleep
        self.last_kwargs = None

    async def create(self, **kwargs):
        self.last_kwargs = kwargs
        if self._sleep:
            await asyncio.sleep(self._sleep)
        if self._exc:
            raise self._exc
        return _Binary(self._content)


class _Audio:
    def __init__(self, speech):
        self.speech = speech


class _FakeClient:
    def __init__(self, content=b"ID3-FAKE-MP3", exc=None, sleep=0.0):
        self.speech = _Speech(content=content, exc=exc, sleep=sleep)
        self.audio = _Audio(self.speech)


# --- provider selection -----------------------------------------------------
def test_default_tts_provider_is_mock() -> None:
    assert isinstance(get_tts_provider(), MockTTSProvider)


def test_missing_key_fails_fast_when_openai_tts(monkeypatch) -> None:
    monkeypatch.setattr(settings, "tts_provider", "openai_tts")
    monkeypatch.setattr(settings, "openai_api_key", "")
    with pytest.raises(RuntimeError):
        get_tts_provider()


def test_real_provider_selected_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "tts_provider", "openai_tts")
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    assert isinstance(get_tts_provider(), RealTTSProvider)


def test_unsupported_audio_format_fails_fast(monkeypatch) -> None:
    monkeypatch.setattr(settings, "tts_provider", "openai_tts")
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(settings, "tts_audio_format", "xyz")
    with pytest.raises(RuntimeError):
        get_tts_provider()


# --- adapter mapping --------------------------------------------------------
@pytest.mark.asyncio
async def test_fake_response_maps_to_tts_result() -> None:
    client = _FakeClient(content=b"ID3-FAKE-MP3")
    provider = RealTTSProvider(api_key="sk-test", client=client)
    res = await provider.synthesize("Klinika 9:00-18:00 ishlaydi.", language="uz-UZ")
    assert isinstance(res, TTSResult)
    assert res.audio_bytes == b"ID3-FAKE-MP3"
    assert res.audio_url is None
    assert res.content_type == "audio/mpeg"  # mp3 default
    assert res.provider_metadata["provider"] == "openai_tts"


@pytest.mark.asyncio
async def test_language_selects_expected_voice() -> None:
    client = _FakeClient()
    provider = RealTTSProvider(
        api_key="sk-test", voice_uz="alloy", voice_ru="nova", client=client
    )
    uz = await provider.synthesize("Salom", language="uz-UZ")
    assert uz.voice == "alloy"
    assert client.speech.last_kwargs["voice"] == "alloy"
    ru = await provider.synthesize("Здравствуйте", language="ru-RU")
    assert ru.voice == "nova"


@pytest.mark.asyncio
async def test_explicit_voice_overrides_language() -> None:
    provider = RealTTSProvider(api_key="sk-test", client=_FakeClient())
    res = await provider.synthesize("Salom", language="uz-UZ", voice="shimmer")
    assert res.voice == "shimmer"


@pytest.mark.asyncio
async def test_wav_format_sets_content_type() -> None:
    provider = RealTTSProvider(api_key="sk-test", audio_format="wav", client=_FakeClient())
    res = await provider.synthesize("Salom", language="uz-UZ")
    assert res.content_type == "audio/wav"


@pytest.mark.asyncio
async def test_timeout_maps_to_timeout_error() -> None:
    client = _FakeClient(sleep=0.2)
    provider = RealTTSProvider(api_key="sk-test", timeout=0.01, client=client)
    with pytest.raises(TTSProviderTimeoutError):
        await provider.synthesize("Salom", language="uz-UZ")


@pytest.mark.asyncio
async def test_provider_error_is_sanitized() -> None:
    client = _FakeClient(exc=ValueError("boom with secret sk-xxx"))
    provider = RealTTSProvider(api_key="sk-test", client=client)
    with pytest.raises(TTSProviderError) as ei:
        await provider.synthesize("Salom", language="uz-UZ")
    assert "sk-xxx" not in str(ei.value)
    assert "secret" not in str(ei.value)


@pytest.mark.asyncio
async def test_too_long_text_is_rejected() -> None:
    provider = RealTTSProvider(api_key="sk-test", max_text_chars=10, client=_FakeClient())
    with pytest.raises(TTSProviderError):
        await provider.synthesize("x" * 11, language="uz-UZ")
