"""AIService — orchestrates SafetyGuard + KB grounding + provider + output review.

DB-free so it can be unit-tested with a mock provider and a stub KB. For factual
clinic questions it prefers the knowledge base and, if the KB lacks the answer,
transfers to a human operator rather than letting the model invent prices or
schedules (TZ §4.2 / §5).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.services.ai.prompts import system_prompt_for
from app.services.ai.provider import (
    AIMessage,
    AIProvider,
    AIRequest,
    ProviderError,
)
from app.services.knowledge.intent import FACTUAL_INTENTS, KBIntent, classify_intent
from app.services.knowledge.service import KnowledgeSearch
from app.services.safety.guard import ReasonCode, SafetyAction, SafetyGuardService
from app.services.safety.reviewer import MockSafetyReviewer, SafetyReviewer

# Safe message when the KB can't ground a factual answer → operator.
_KB_INSUFFICIENT_UZ = (
    "Kechirasiz, bu ma'lumotni aniq tasdiqlay olmayman. Aniqlik uchun sizni operatorga ulayman."
)
_KB_INSUFFICIENT_RU = (
    "Извините, я не могу точно подтвердить эту информацию. Для уточнения я соединю вас с оператором."
)
_PROVIDER_DOWN_UZ = (
    "Kechirasiz, hozir javob bera olmadim. Sizni operatorga ulayman."
)
_PROVIDER_DOWN_RU = (
    "Извините, сейчас не удалось ответить. Я соединю вас с оператором."
)


@dataclass
class AIResult:
    reply: str
    action: SafetyAction
    category: ReasonCode
    sources: list[dict] = field(default_factory=list)

    @property
    def reason_code(self) -> ReasonCode:
        return self.category

    @property
    def transfer_requested(self) -> bool:
        return self.action in (SafetyAction.TRANSFER, SafetyAction.EMERGENCY)


class AIService:
    def __init__(
        self,
        provider: AIProvider,
        knowledge: KnowledgeSearch,
        guard: SafetyGuardService | None = None,
        reviewer: SafetyReviewer | None = None,
    ) -> None:
        self._provider = provider
        self._knowledge = knowledge
        self._guard = guard or SafetyGuardService()
        self._reviewer = reviewer or MockSafetyReviewer()

    async def respond(
        self,
        *,
        history: list[AIMessage],
        user_text: str,
        language: str,
        ai_confidence: float | None = None,
    ) -> AIResult:
        # 1) Safety first — never reaches the provider on a blocked request.
        decision = self._guard.evaluate(user_text, language)
        if decision.action is not SafetyAction.ALLOW:
            message = decision.message_for(language)
            assert message is not None
            return AIResult(message, decision.action, decision.reason_code)

        # 2) Ground factual questions in the KB.
        intent = classify_intent(user_text)
        matches = await self._knowledge.search(user_text, language, intent=intent)

        # 3) Anti-hallucination: a factual question with no KB data → operator.
        if not matches and intent in FACTUAL_INTENTS:
            ru = language.startswith("ru")
            reason = (
                ReasonCode.PRICE_OR_SCHEDULE_UNCLEAR
                if intent in (KBIntent.PRICE, KBIntent.SCHEDULE)
                else ReasonCode.LOW_CONFIDENCE
            )
            return AIResult(
                _KB_INSUFFICIENT_RU if ru else _KB_INSUFFICIENT_UZ,
                SafetyAction.TRANSFER,
                reason,
            )

        # 4) Generate, grounded in the KB content. Provider failure/timeout -> operator.
        context = [m.content for m in matches]
        try:
            response = await self._provider.generate(
                AIRequest(
                    system=system_prompt_for(language),
                    messages=[*history, AIMessage(role="user", content=user_text)],
                    context=context,
                    language=language,
                )
            )
        except ProviderError:
            ru = language.startswith("ru")
            return AIResult(
                _PROVIDER_DOWN_RU if ru else _PROVIDER_DOWN_UZ,
                SafetyAction.TRANSFER,
                ReasonCode.LOW_CONFIDENCE,
            )
        reply = response.message

        # 5) Defense-in-depth: validate the generated output.
        review = await self._reviewer.review(reply, language)
        if not review.is_safe:
            message = review.message_for(language)
            assert message is not None
            action = SafetyAction.EMERGENCY if review.is_emergency else SafetyAction.TRANSFER
            return AIResult(message, action, review.reason_code)

        # 6) Low-confidence transfer (TZ §4.6) — provider-reported confidence wins.
        confidence = response.confidence if response.confidence is not None else ai_confidence
        conf = self._guard.evaluate_confidence(confidence, language)
        if conf.action is not SafetyAction.ALLOW:
            message = conf.message_for(language)
            assert message is not None
            return AIResult(message, conf.action, conf.reason_code)

        sources = [{"id": m.id, "title": m.title} for m in matches]
        return AIResult(reply, SafetyAction.ALLOW, ReasonCode.NONE, sources=sources)
