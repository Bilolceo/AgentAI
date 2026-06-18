"""Streaming STT architecture (mock-first) for Twilio Media Streams.

Provider-first, like the non-streaming STTProvider: a StreamingSTTProvider opens a
per-stream session that accepts audio frames and emits partial/final transcript
events. The mock is deterministic and decodes NO real speech, so tests and the
spike need no external/paid provider.

Safety: the raw audio payload is held only transiently to hand to the provider; it
is NEVER logged or persisted. Only counts + the recognized transcript text (not
audio) are summarized.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

_CYRILLIC = re.compile(r"[а-яёА-ЯЁ]")


def _detect_language(text: str) -> str:
    return "ru-RU" if _CYRILLIC.search(text) else "uz-UZ"


# --- data ------------------------------------------------------------------
@dataclass
class StreamingAudioFrame:
    stream_sid: Optional[str]
    call_sid: Optional[str]
    sequence_number: Optional[int]
    timestamp_ms: Optional[int]
    payload_bytes: bytes  # decoded audio, transient (never logged/persisted)
    codec: str = "audio/x-mulaw"
    track: Optional[str] = None


@dataclass
class TranscriptEvent:
    text: str
    language: str
    is_final: bool
    provider: str
    confidence: Optional[float] = None
    timestamp_ms: Optional[int] = None
    metadata: dict = field(default_factory=dict)
    # Stable identity for a FINAL event. Providers MUST set a monotonic/unique id
    # per final so the turn layer can dedup an actual re-delivery WITHOUT conflating
    # two separate utterances that happen to share the same text. May be None for
    # partials (they never dedup) or legacy providers (see StreamingTurnManager).
    event_id: Optional[str] = None


@dataclass
class StreamingContext:
    stream_sid: Optional[str]
    call_sid: Optional[str] = None
    language: Optional[str] = None
    params: dict = field(default_factory=dict)  # Twilio customParameters (safe)


class StreamingSTTError(Exception):
    """Streaming STT failed; the session is marked degraded (no crash)."""


# --- provider / session interfaces -----------------------------------------
class StreamingSTTSession(ABC):
    """One streaming recognition session, owned per stream_sid."""

    @abstractmethod
    async def accept_audio_frame(self, frame: StreamingAudioFrame) -> list[TranscriptEvent]:
        raise NotImplementedError

    @abstractmethod
    async def finish_stream(self) -> list[TranscriptEvent]:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError


class StreamingSTTProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    def start_stream(self, context: StreamingContext) -> StreamingSTTSession:
        """Open a session for one stream. Real providers may connect lazily."""
        raise NotImplementedError


# --- mock provider ---------------------------------------------------------
class _MockStreamingSession(StreamingSTTSession):
    """Deterministic: emits one partial near the middle and one final at N frames.

    The phrase comes from customParameters["test_phrase"] (or a default), so tests
    are fully deterministic without decoding any real audio.
    """

    def __init__(self, context: StreamingContext, final_after_frames: int, phrase: str) -> None:
        self._final_after = max(1, final_after_frames)
        self._phrase = phrase or "Salom"
        self._language = context.language or _detect_language(self._phrase)
        self._n = 0
        self._partial_emitted = False
        self._final_emitted = False
        # Per-session token + monotonic counter -> a stable, unique id per FINAL.
        self._token = context.stream_sid or "mock-stream"
        self._final_seq = 0

    async def accept_audio_frame(self, frame: StreamingAudioFrame) -> list[TranscriptEvent]:
        self._n += 1
        out: list[TranscriptEvent] = []
        half = max(1, self._final_after // 2)
        if not self._final_emitted and not self._partial_emitted and self._n >= half \
                and self._n < self._final_after:
            self._partial_emitted = True
            first = self._phrase.split()[0] if self._phrase.split() else self._phrase
            out.append(self._event(first, is_final=False, confidence=None))
        if not self._final_emitted and self._n >= self._final_after:
            self._final_emitted = True
            out.append(self._event(self._phrase, is_final=True, confidence=0.9))
        return out

    async def finish_stream(self) -> list[TranscriptEvent]:
        if not self._final_emitted:
            self._final_emitted = True
            return [self._event(self._phrase, is_final=True, confidence=0.9)]
        return []

    async def close(self) -> None:
        return None

    def _event(self, text: str, *, is_final: bool, confidence: Optional[float]) -> TranscriptEvent:
        event_id = None
        if is_final:
            # Monotonic, unique per session: two distinct finals never collide, but a
            # re-delivery of the same final keeps the same id.
            event_id = f"{self._token}:final:{self._final_seq}"
            self._final_seq += 1
        return TranscriptEvent(
            text=text,
            language=self._language,
            is_final=is_final,
            provider="mock",
            confidence=confidence,
            timestamp_ms=None,
            metadata={"mode": "mock"},
            event_id=event_id,
        )


class MockStreamingSTTProvider(StreamingSTTProvider):
    name = "mock"

    def __init__(self, *, final_after_frames: int = 25) -> None:
        self._final_after_frames = max(1, final_after_frames)

    def start_stream(self, context: StreamingContext) -> StreamingSTTSession:
        phrase = str((context.params or {}).get("test_phrase") or "Salom")
        return _MockStreamingSession(context, self._final_after_frames, phrase)


# --- session orchestration -------------------------------------------------
class StreamingSTTSessionService:
    """Owns one streaming STT session, buffers frame COUNTS (never raw audio),
    enforces memory limits, and tracks the partial/final transcript safely."""

    def __init__(
        self,
        provider: StreamingSTTProvider,
        *,
        max_frames: int = 10_000,
        max_bytes: int = 8_000_000,
    ) -> None:
        self._provider = provider
        self._max_frames = max_frames
        self._max_bytes = max_bytes
        self._session: Optional[StreamingSTTSession] = None
        self.frames = 0
        self.bytes = 0
        self.partial_count = 0
        self.final_transcripts: list[TranscriptEvent] = []
        self.degraded = False
        self.over_limit = False
        self.errors = 0
        self._finished = False

    @property
    def final_transcript(self) -> Optional[TranscriptEvent]:
        """The most recent final transcript, if any."""
        return self.final_transcripts[-1] if self.final_transcripts else None

    async def start(
        self,
        *,
        stream_sid: Optional[str],
        call_sid: Optional[str] = None,
        language: Optional[str] = None,
        params: Optional[dict] = None,
    ) -> None:
        ctx = StreamingContext(
            stream_sid=stream_sid, call_sid=call_sid, language=language, params=params or {}
        )
        try:
            self._session = self._provider.start_stream(ctx)
        except Exception:  # provider open failed -> degrade, never crash
            self.degraded = True
            self.errors += 1

    async def push_frame(self, frame: StreamingAudioFrame) -> list[TranscriptEvent]:
        if self._session is None or self.degraded or self._finished:
            return []
        self.frames += 1
        self.bytes += len(frame.payload_bytes or b"")
        if self.frames > self._max_frames or self.bytes > self._max_bytes:
            self.over_limit = True
            return []
        try:
            events = await self._session.accept_audio_frame(frame)
        except Exception:  # provider error -> degrade, do not crash the socket
            self.degraded = True
            self.errors += 1
            return []
        return self._absorb(events)

    async def finish(self) -> list[TranscriptEvent]:
        if self._finished:
            return []
        self._finished = True
        events: list[TranscriptEvent] = []
        if self._session is not None and not self.degraded:
            try:
                events = await self._session.finish_stream()
            except Exception:
                self.degraded = True
                self.errors += 1
                events = []
            try:
                await self._session.close()
            except Exception:
                pass
        return self._absorb(events)

    def _absorb(self, events: list[TranscriptEvent]) -> list[TranscriptEvent]:
        for e in events:
            if e.is_final:
                self.final_transcripts.append(e)
            else:
                self.partial_count += 1
        return events

    def summary(self, *, stopped_reason: str = "") -> dict:
        """Safe summary for TelephonyStream.stream_metadata.

        Counts + recognized transcript TEXT only. NEVER includes raw audio or any
        base64 payload.
        """
        if not stopped_reason:
            stopped_reason = (
                "over_limit" if self.over_limit
                else "degraded" if self.degraded
                else "finished" if self._finished
                else "active"
            )
        return {
            "provider": getattr(self._provider, "name", "mock"),
            "frames_processed": self.frames,
            "bytes_processed": self.bytes,
            "partial_count": self.partial_count,
            "final_count": len(self.final_transcripts),
            "final_transcripts": [
                {"text": f.text, "language": f.language, "confidence": f.confidence}
                for f in self.final_transcripts
            ],
            "stopped_reason": stopped_reason,
            "errors": self.errors,
            "degraded": self.degraded,
            "over_limit": self.over_limit,
        }
