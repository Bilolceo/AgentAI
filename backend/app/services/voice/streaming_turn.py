"""StreamingTurnService — route a FINAL streaming transcript through the existing
AI/safety pipeline and produce a SAFE, persistable turn.

Only FINAL transcripts reach this layer. Partial transcripts NEVER call the AI.
The full text safety pipeline is preserved end to end (pre-LLM medical guard, KB
grounding / anti-hallucination, post-LLM reviewer, operator-transfer decision)
because we reuse CallSessionService.handle_message — the same path used by the
text simulation and the Twilio Gather flow.

Safety/scope:
  - no raw audio or base64 is ever read or stored here (only the recognized text);
  - this produces an AI TEXT turn only. There is NO streaming TTS and NO audio is
    sent back to Twilio yet;
  - run_turn never raises: provider/AI/DB failures map to a degraded turn so the
    WebSocket cannot crash.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.core.logging import get_logger
from app.services.call.session import CallSessionService, MessageOutcome
from app.services.voice.streaming_stt import TranscriptEvent

log = get_logger("streaming_turn")

_MAX_SOURCES = 10  # cap persisted KB sources per turn (bounds metadata growth)


class StreamingTurnService:
    """Run one FINAL transcript through CallSessionService and shape a safe turn."""

    def __init__(self, css: CallSessionService, *, max_transcript_chars: int = 2000) -> None:
        self._css = css
        self._max_transcript_chars = max(1, max_transcript_chars)

    async def run_turn(
        self,
        *,
        call_session_id: int,
        stream_id: Optional[int],
        transcript: TranscriptEvent,
    ) -> dict:
        """Process ONE final transcript; return a SAFE turn dict (never raises).

        Caller must only pass FINAL transcripts. The transcript text is capped to
        ``max_transcript_chars`` before it reaches the pipeline.
        """
        raw = transcript.text or ""
        truncated = len(raw) > self._max_transcript_chars
        text = raw[: self._max_transcript_chars].strip()
        base = self._base(transcript, text=text, truncated=truncated)
        if not text:
            return {**base, "degraded": True, "error": "empty_transcript"}

        try:
            outcome: MessageOutcome = await self._css.handle_message(
                call_id=call_session_id, text=text, language=transcript.language or None
            )
        except Exception:  # AI/provider/DB failure -> degraded turn, never crash the WS
            # A DB/transaction error can leave the shared AsyncSession in a pending
            # rollback state; clean it so the later attach_streaming_summary commit
            # (in _finalize) still succeeds. Rollback failure must not crash the WS.
            try:
                await self._css.rollback()
            except Exception:
                log.warning("streaming_turn_rollback_failed", stream_id=stream_id)
            log.warning("streaming_turn_failed", stream_id=stream_id, call_session_id=call_session_id)
            return {**base, "degraded": True, "error": "pipeline_error"}

        return {
            **base,
            "ai_text": outcome.reply,
            "action": outcome.action,
            "reason_code": outcome.reason_code,
            "transferred": outcome.transferred,
            "transfer_reason": outcome.transfer_reason,
            "priority": outcome.priority,
            "callback_required": outcome.callback_required,
            "language": outcome.language,
            "sources": [
                {"id": s.get("id"), "title": s.get("title")}
                for s in (outcome.sources or [])[:_MAX_SOURCES]
            ],
            "degraded": False,
            "error": None,
        }

    def _base(self, transcript: TranscriptEvent, *, text: str, truncated: bool) -> dict:
        """Default/safe turn shape (no raw audio, only recognized transcript text)."""
        return {
            "transcript_text": text,
            "transcript_language": transcript.language,
            "transcript_confidence": transcript.confidence,
            "transcript_truncated": truncated,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ai_text": "",
            "action": None,
            "reason_code": None,
            "transferred": False,
            "transfer_reason": None,
            "priority": None,
            "callback_required": False,
            "language": transcript.language,
            "sources": [],
        }


class StreamingTurnManager:
    """Owns AI-turn execution for one stream.

    Enforces a per-stream turn cap, de-duplicates identical final events (so a
    repeated final does not double-call the AI), and accumulates SAFE turn dicts
    for the stream summary. Partials are rejected here as a second guard.
    """

    def __init__(
        self,
        service: StreamingTurnService,
        *,
        call_session_id: int,
        stream_id: Optional[int],
        max_turns: int = 50,
    ) -> None:
        self._service = service
        self._call_session_id = call_session_id
        self._stream_id = stream_id
        self._max_turns = max(1, max_turns)
        self.turns: list[dict] = []
        self.over_limit = False
        self._seen_ids: set = set()  # stable event_ids already processed
        self._last_obj: Optional[TranscriptEvent] = None  # immediate-redelivery guard

    async def on_final(self, transcript: TranscriptEvent) -> Optional[dict]:
        """Run an AI turn for a FINAL transcript (deduped + capped). Returns the
        turn dict, or None when ignored (partial / duplicate / over the cap)."""
        if not transcript.is_final:
            return None  # partial transcripts NEVER reach the AI
        # Dedup the RE-DELIVERY of one final, never two separate utterances that
        # share the same text. Prefer the provider's stable event_id. When a
        # (legacy) provider omits it, fall back conservatively to OBJECT identity
        # via `is` (holding a reference, so this is reliable - unlike id(), whose
        # value can be reused after GC): only the exact same object delivered twice
        # in a row is suppressed; distinct utterances each create a turn.
        if transcript.event_id is not None:
            if transcript.event_id in self._seen_ids:
                return None
            self._seen_ids.add(transcript.event_id)
        elif transcript is self._last_obj:
            return None
        self._last_obj = transcript
        if len(self.turns) >= self._max_turns:
            self.over_limit = True
            return None
        turn = await self._service.run_turn(
            call_session_id=self._call_session_id,
            stream_id=self._stream_id,
            transcript=transcript,
        )
        turn["order"] = len(self.turns)
        self.turns.append(turn)
        return turn

    def summary(self) -> dict:
        """Turn block merged into TelephonyStream.stream_metadata.streaming_stt."""
        return {
            "turns": self.turns,
            "turn_count": len(self.turns),
            "turns_over_limit": self.over_limit,
        }
