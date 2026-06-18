"""ClaudeAIProvider + provider selection (fake client; no real API calls)."""
from __future__ import annotations

import pytest

from app.api.deps import get_ai_provider
from app.core.config import settings
from app.services.ai.provider import (
    AIRequest,
    AIResponse,
    ClaudeAIProvider,
    MockAIProvider,
    ProviderError,
    ProviderTimeoutError,
)
from app.services.ai.service import AIService
from app.services.knowledge.service import KBMatch
from app.services.safety.guard import SafetyAction


# --- fakes ------------------------------------------------------------------
class _Block:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _Resp:
    def __init__(self, text: str) -> None:
        self.content = [_Block(text)]
        self.model = "claude-sonnet-4-6"
        self.stop_reason = "end_turn"


class _FakeMessages:
    def __init__(self, text: str) -> None:
        self._text = text

    async def create(self, **kwargs):
        return _Resp(self._text)


class _FakeClient:
    def __init__(self, text: str) -> None:
        self.messages = _FakeMessages(text)


class _StubKnowledge:
    async def search(self, query: str, language: str, intent=None) -> list[KBMatch]:
        return [KBMatch(id=1, title="Ish vaqti", content="Klinika 09:00-18:00.", category="clinic_info")]


class _TimeoutProvider:
    async def generate(self, request: AIRequest) -> AIResponse:
        raise ProviderTimeoutError("timeout")


class _UnsafeProvider:
    async def generate(self, request: AIRequest) -> AIResponse:
        return AIResponse(message="Sizga antibiotik tabletka iching, kuniga 3 mahal")


# --- provider selection -----------------------------------------------------
def test_default_provider_is_mock() -> None:
    assert isinstance(get_ai_provider(), MockAIProvider)


def test_missing_api_key_raises_when_claude(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_provider", "claude")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    with pytest.raises(RuntimeError):
        get_ai_provider()


def test_claude_provider_built_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_provider", "claude")
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-test")
    assert isinstance(get_ai_provider(), ClaudeAIProvider)


# --- Claude provider mapping ------------------------------------------------
@pytest.mark.asyncio
async def test_claude_provider_maps_fake_response() -> None:
    provider = ClaudeAIProvider(
        model="claude-sonnet-4-6", api_key="sk-test", client=_FakeClient("Klinika 9:00-18:00 ishlaydi.")
    )
    resp = await provider.generate(
        AIRequest(system="sys", messages=[], context=["Klinika 9:00-18:00 ishlaydi."], language="uz-UZ")
    )
    assert isinstance(resp, AIResponse)
    assert resp.message == "Klinika 9:00-18:00 ishlaydi."
    assert resp.raw_metadata["provider"] == "claude"
    assert resp.raw_metadata["model"] == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_claude_provider_error_is_wrapped() -> None:
    class _Boom:
        class messages:
            @staticmethod
            async def create(**kwargs):
                raise ValueError("api exploded with secret sk-xxx")

    provider = ClaudeAIProvider(model="m", api_key="sk-test", client=_Boom())
    with pytest.raises(ProviderError) as ei:
        await provider.generate(AIRequest(system="s", messages=[], language="uz-UZ"))
    # error message must not leak the underlying detail / secrets
    assert "sk-xxx" not in str(ei.value)


# --- AIService integration with fake providers ------------------------------
@pytest.mark.asyncio
async def test_provider_timeout_maps_to_operator_transfer() -> None:
    svc = AIService(provider=_TimeoutProvider(), knowledge=_StubKnowledge())
    result = await svc.respond(history=[], user_text="Salom, yordam kerak", language="uz-UZ")
    assert result.action is SafetyAction.TRANSFER
    assert result.transfer_requested


@pytest.mark.asyncio
async def test_unsafe_claude_output_blocked_by_reviewer() -> None:
    svc = AIService(provider=_UnsafeProvider(), knowledge=_StubKnowledge())
    result = await svc.respond(history=[], user_text="Salom, yordam kerak", language="uz-UZ")
    assert result.action is SafetyAction.TRANSFER
    assert "antibiotik" not in result.reply


@pytest.mark.asyncio
async def test_claude_pipeline_safe_grounded_answer() -> None:
    provider = ClaudeAIProvider(
        model="m", api_key="sk-test", client=_FakeClient("Klinika 09:00 dan 18:00 gacha ishlaydi.")
    )
    svc = AIService(provider=provider, knowledge=_StubKnowledge())
    result = await svc.respond(history=[], user_text="Ish vaqtingiz qanday?", language="uz-UZ")
    assert result.action is SafetyAction.ALLOW
    assert "09:00" in result.reply
    assert result.sources  # KB grounding sources present
