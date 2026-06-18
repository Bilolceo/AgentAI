"""Real STT (OpenAI Whisper) adapter + provider selection (fake client only)."""
from __future__ import annotations

import asyncio

import pytest

from app.api.deps import get_stt_provider
from app.core.config import settings
from app.services.voice.stt import (
    MockSTTProvider,
    RealSTTProvider,
    STTProviderError,
    STTProviderTimeoutError,
    STTResult,
)


# --- fake OpenAI client -----------------------------------------------------
class _Resp:
    def __init__(self, text, language, duration):
        self.text = text
        self.language = language
        self.duration = duration


class _Transcriptions:
    def __init__(self, resp=None, exc=None, sleep=0.0):
        self._resp, self._exc, self._sleep = resp, exc, sleep

    async def create(self, **kwargs):
        if self._sleep:
            await asyncio.sleep(self._sleep)
        if self._exc:
            raise self._exc
        return self._resp


class _Audio:
    def __init__(self, transcriptions):
        self.transcriptions = transcriptions


class _FakeClient:
    def __init__(self, resp=None, exc=None, sleep=0.0):
        self.audio = _Audio(_Transcriptions(resp=resp, exc=exc, sleep=sleep))


# --- provider selection -----------------------------------------------------
def test_default_stt_provider_is_mock() -> None:
    assert isinstance(get_stt_provider(), MockSTTProvider)


def test_missing_key_fails_fast_when_whisper(monkeypatch) -> None:
    monkeypatch.setattr(settings, "stt_provider", "openai_whisper")
    monkeypatch.setattr(settings, "openai_api_key", "")
    with pytest.raises(RuntimeError):
        get_stt_provider()


def test_real_provider_selected_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "stt_provider", "openai_whisper")
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    assert isinstance(get_stt_provider(), RealSTTProvider)


# --- adapter mapping --------------------------------------------------------
@pytest.mark.asyncio
async def test_fake_response_maps_to_stt_result() -> None:
    client = _FakeClient(_Resp("Klinika manzili qayerda?", "uzbek", 1.5))
    provider = RealSTTProvider(api_key="sk-test", client=client)
    res = await provider.transcribe(b"fake-audio", content_type="audio/wav")
    assert isinstance(res, STTResult)
    assert res.text == "Klinika manzili qayerda?"
    assert res.language == "uz-UZ"
    assert res.confidence is None  # Whisper has no confidence
    assert res.duration_ms == 1500
    assert res.provider_metadata["provider"] == "openai_whisper"


@pytest.mark.asyncio
async def test_russian_response_maps_to_ru_locale() -> None:
    client = _FakeClient(_Resp("Сколько стоит приём?", "russian", 2.0))
    provider = RealSTTProvider(api_key="sk-test", client=client)
    res = await provider.transcribe(b"fake", content_type="audio/mpeg")
    assert res.language == "ru-RU"


@pytest.mark.asyncio
async def test_timeout_maps_to_timeout_error() -> None:
    client = _FakeClient(sleep=0.2)
    provider = RealSTTProvider(api_key="sk-test", timeout=0.01, client=client)
    with pytest.raises(STTProviderTimeoutError):
        await provider.transcribe(b"fake")


@pytest.mark.asyncio
async def test_provider_error_is_sanitized() -> None:
    client = _FakeClient(exc=ValueError("boom with secret sk-xxx"))
    provider = RealSTTProvider(api_key="sk-test", client=client)
    with pytest.raises(STTProviderError) as ei:
        await provider.transcribe(b"fake")
    assert "sk-xxx" not in str(ei.value)
    assert "secret" not in str(ei.value)


@pytest.mark.asyncio
async def test_text_override_bypasses_real_api() -> None:
    # No client needed; text_hint short-circuits without touching the API.
    provider = RealSTTProvider(api_key="sk-test")
    res = await provider.transcribe(b"", text_hint="Ish vaqtingiz qanday?")
    assert res.text == "Ish vaqtingiz qanday?"
    assert res.provider_metadata["mode"] == "text_override"
