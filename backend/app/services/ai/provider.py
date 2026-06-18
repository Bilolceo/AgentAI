"""AI provider interface + implementations.

Provider-first design: the rest of the system depends only on `AIProvider`.
`MockAIProvider` is deterministic (tests + default). `ClaudeAIProvider` is the
real implementation behind the AI_PROVIDER=claude flag; it is constructed with an
injectable client so unit tests never touch the network.
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AIMessage:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class AIRequest:
    system: str
    messages: list[AIMessage]
    context: list[str] = field(default_factory=list)  # KB content snippets
    language: str = "uz-UZ"


@dataclass
class AIResponse:
    message: str
    confidence: Optional[float] = None
    used_sources: list[dict] = field(default_factory=list)
    raw_metadata: dict = field(default_factory=dict)


class ProviderError(Exception):
    """Provider failed (network/API error). Mapped to a safe operator transfer."""


class ProviderTimeoutError(ProviderError):
    """Provider timed out."""


class AIProvider(ABC):
    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        raise NotImplementedError


class MockAIProvider(AIProvider):
    """Deterministic provider for tests and the pre-integration simulation.

    Echoes grounded KB context when available, otherwise a generic clinic reply.
    Never produces medical advice (the safety guard gates input before this runs).
    """

    async def generate(self, request: AIRequest) -> AIResponse:
        if request.context:
            message = request.context[0]
        elif request.language.startswith("ru"):
            message = "Спасибо за обращение. Чем я могу помочь по работе клиники?"
        else:
            message = "Murojaatingiz uchun rahmat. Klinika bo'yicha qanday yordam bera olaman?"
        return AIResponse(message=message, confidence=None, used_sources=[], raw_metadata={"provider": "mock"})


_FAITHFULNESS_UZ = (
    "\n\nQOIDALAR:\n"
    "- Klinika faktlari (manzil, ish vaqti, narx, shifokor, xizmat) bo'yicha FAQAT quyidagi "
    "bilim bazasidan foydalaning. Narx, jadval, shifokor yoki manzilni o'zingizdan to'qib chiqarmang.\n"
    "- Bilim bazasida javob bo'lmasa: \"Operator sizga yordam beradi\" deb ayting.\n"
    "- Tibbiy tashxis qo'ymang; dori, doza yoki davolashni tavsiya etmang.\n"
    "- Favqulodda holatda 103 raqamini ayting.\n"
    "- Javob qisqa va telefon suhbatiga mos bo'lsin.\n"
)
_FAITHFULNESS_RU = (
    "\n\nПРАВИЛА:\n"
    "- По фактам клиники (адрес, часы работы, цены, врачи, услуги) используйте ТОЛЬКО базу знаний ниже. "
    "Не выдумывайте цены, расписание, врачей или адрес.\n"
    "- Если ответа нет в базе знаний: скажите, что поможет оператор.\n"
    "- Не ставьте диагноз; не рекомендуйте лекарства, дозировки или лечение.\n"
    "- В экстренной ситуации назовите номер 103.\n"
    "- Ответ должен быть коротким и подходящим для телефонного разговора.\n"
)


class ClaudeAIProvider(AIProvider):
    """Anthropic Claude implementation (enabled via AI_PROVIDER=claude)."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        timeout: float = 15.0,
        max_tokens: int = 1024,
        temperature: Optional[float] = None,
        client=None,
    ) -> None:
        self._model = model
        self._api_key = api_key
        self._timeout = timeout
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._client = client  # injectable for tests; created lazily otherwise

    def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic  # imported lazily; needs the SDK + key

            self._client = AsyncAnthropic(api_key=self._api_key)
        return self._client

    def _build_system(self, request: AIRequest) -> str:
        ru = request.language.startswith("ru")
        system = request.system + (_FAITHFULNESS_RU if ru else _FAITHFULNESS_UZ)
        if request.context:
            joined = "\n".join(f"- {c}" for c in request.context)
            label = "База знаний:" if ru else "Bilim bazasi:"
            system = f"{system}\n{label}\n{joined}"
        return system

    async def generate(self, request: AIRequest) -> AIResponse:
        client = self._get_client()
        kwargs = dict(
            model=self._model,
            max_tokens=self._max_tokens,
            system=self._build_system(request),
            thinking={"type": "disabled"},  # real-time latency
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
        )
        if self._temperature is not None:
            kwargs["temperature"] = self._temperature
        try:
            resp = await asyncio.wait_for(client.messages.create(**kwargs), timeout=self._timeout)
        except asyncio.TimeoutError as exc:
            raise ProviderTimeoutError("AI provider timed out") from exc
        except Exception as exc:  # never include secrets/payload in the message
            raise ProviderError(f"AI provider error: {type(exc).__name__}") from exc

        text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
        return AIResponse(
            message=text,
            confidence=None,  # Claude does not return a calibrated confidence
            used_sources=[],
            raw_metadata={
                "provider": "claude",
                "model": getattr(resp, "model", self._model),
                "stop_reason": getattr(resp, "stop_reason", None),
            },
        )
