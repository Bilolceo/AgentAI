"""Streaming AI turns: a FINAL transcript routes through the full AI/safety
pipeline and the safe turn is persisted. Partials never call the AI.

Unit tests cover the StreamingTurnService/Manager (call-count, dedup, max-turns,
truncation, degraded) and the real pipeline (emergency/103, unsafe-blocked, KB
sources, operator transfer). One WebSocket integration test drives an emergency
final end to end and asserts the persisted turn via a spy (no cross-loop DB read,
no real audio).
"""
from __future__ import annotations

import base64

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from app.core.db import Base, get_session
from app.main import app
from app.models.admin_user import AdminUser
from app.models.audit_log import AuditLog
from app.models.call import Call
from app.models.callback_task import CallbackTask
from app.models.knowledge_item import KnowledgeItem
from app.models.telephony_call import TelephonyCall
from app.models.telephony_stream import TelephonyStream
from app.models.transcript import Transcript
from app.services.ai.provider import MockAIProvider
from app.services.ai.service import AIService
from app.services.audit.log import AuditLogService
from app.services.call.session import CallSessionService, MessageOutcome
from app.services.knowledge.service import KBMatch
from app.services.operator.availability import MockOperatorAvailability, OperatorState
from app.services.operator.transfer import OperatorTransferDecisionService
from app.services.telephony.stream import TelephonyStreamService
from app.services.telephony.twilio import TwilioTelephonyProvider
from app.services.voice.streaming_stt import TranscriptEvent
from app.services.voice.streaming_turn import StreamingTurnManager, StreamingTurnService

API = "/api/v1"
WS_URL = f"{API}/telephony/twilio/media-stream"

_WS_PROVIDER = TwilioTelephonyProvider(
    auth_token="ws-secret", public_base_url="https://x", validate_signature=False
)

# Full relational table set (mirrors conftest; pgvector knowledge_chunks skipped).
_TABLES = [
    Call.__table__,
    Transcript.__table__,
    AuditLog.__table__,
    CallbackTask.__table__,
    KnowledgeItem.__table__,
    AdminUser.__table__,
    TelephonyCall.__table__,
    TelephonyStream.__table__,
]


def _final(
    text="Klinika manzili qayerda", *, language="uz-UZ", ts=10, conf=0.9, event_id="ev-1"
) -> TranscriptEvent:
    return TranscriptEvent(
        text=text, language=language, is_final=True, provider="mock",
        confidence=conf, timestamp_ms=ts, event_id=event_id,
    )


# --- stub CallSessionService for call-count / dedup / cap tests --------------
class _CountingCSS:
    def __init__(
        self, outcome: MessageOutcome | None = None, *, raises: bool = False,
        rollback_raises: bool = False,
    ) -> None:
        self.calls: list[dict] = []
        self._outcome = outcome
        self._raises = raises
        self._rollback_raises = rollback_raises
        self.rolled_back = False

    async def handle_message(self, *, call_id, text, language=None) -> MessageOutcome:
        self.calls.append({"call_id": call_id, "text": text, "language": language})
        if self._raises:
            raise RuntimeError("pipeline boom")
        return self._outcome or MessageOutcome(
            reply="ok", action="allow", reason_code="none", transferred=False,
            language=language or "uz-UZ",
        )

    async def rollback(self) -> None:
        self.rolled_back = True
        if self._rollback_raises:
            raise RuntimeError("rollback boom")


def _manager(css, *, max_turns=50, max_chars=2000) -> tuple[StreamingTurnManager, _CountingCSS]:
    svc = StreamingTurnService(css, max_transcript_chars=max_chars)
    mgr = StreamingTurnManager(svc, call_session_id=1, stream_id=7, max_turns=max_turns)
    return mgr, css


# --- unit: turn routing rules ------------------------------------------------
@pytest.mark.asyncio
async def test_partial_transcript_never_calls_ai() -> None:
    css = _CountingCSS()
    mgr, _ = _manager(css)
    partial = TranscriptEvent(text="Klin", language="uz-UZ", is_final=False, provider="mock")
    assert await mgr.on_final(partial) is None
    assert css.calls == []  # partial must never reach the AI


@pytest.mark.asyncio
async def test_final_transcript_calls_ai_once() -> None:
    css = _CountingCSS()
    mgr, _ = _manager(css)
    turn = await mgr.on_final(_final())
    assert turn is not None
    assert len(css.calls) == 1
    assert len(mgr.turns) == 1
    assert mgr.turns[0]["order"] == 0


@pytest.mark.asyncio
async def test_same_event_id_delivered_twice_calls_ai_once() -> None:
    css = _CountingCSS()
    mgr, _ = _manager(css)
    # Two SEPARATE objects but the SAME final event_id == a re-delivery, not a turn.
    await mgr.on_final(_final(text="Salom", event_id="f-7"))
    assert await mgr.on_final(_final(text="Salom", event_id="f-7")) is None
    assert len(css.calls) == 1
    assert len(mgr.turns) == 1


@pytest.mark.asyncio
async def test_distinct_event_ids_same_text_create_two_turns() -> None:
    css = _CountingCSS()
    mgr, _ = _manager(css)
    # Same text, but distinct finals (different event_id) -> two separate turns.
    await mgr.on_final(_final(text="Ha", event_id="f-1"))
    await mgr.on_final(_final(text="Ha", event_id="f-2"))
    assert len(css.calls) == 2
    assert [t["order"] for t in mgr.turns] == [0, 1]


@pytest.mark.asyncio
async def test_same_object_without_event_id_dedups_conservatively() -> None:
    css = _CountingCSS()
    mgr, _ = _manager(css)
    ev = _final(event_id=None)  # legacy provider: no event_id
    await mgr.on_final(ev)
    assert await mgr.on_final(ev) is None  # exact same object re-delivered -> one turn
    assert len(css.calls) == 1


@pytest.mark.asyncio
async def test_distinct_objects_without_event_id_each_create_turn() -> None:
    css = _CountingCSS()
    mgr, _ = _manager(css)
    # No event_id and distinct objects (separate utterances) -> not deduped by text.
    await mgr.on_final(_final(text="Ha", event_id=None))
    await mgr.on_final(_final(text="Ha", event_id=None))
    assert len(css.calls) == 2


@pytest.mark.asyncio
async def test_max_turns_enforced() -> None:
    css = _CountingCSS()
    mgr, _ = _manager(css, max_turns=1)
    await mgr.on_final(_final(text="Bir", event_id="f-1"))
    assert await mgr.on_final(_final(text="Ikki", event_id="f-2")) is None  # over the cap
    assert len(css.calls) == 1
    assert mgr.over_limit is True
    assert mgr.summary()["turns_over_limit"] is True


@pytest.mark.asyncio
async def test_transcript_truncated_to_cap() -> None:
    css = _CountingCSS()
    mgr, _ = _manager(css, max_chars=10)
    await mgr.on_final(_final(text="x" * 50))
    assert len(css.calls[0]["text"]) == 10  # pipeline received the capped text
    assert mgr.turns[0]["transcript_truncated"] is True


@pytest.mark.asyncio
async def test_empty_transcript_is_degraded_not_called() -> None:
    css = _CountingCSS()
    mgr, _ = _manager(css)
    turn = await mgr.on_final(_final(text="   "))
    assert css.calls == []
    assert turn["degraded"] is True and turn["error"] == "empty_transcript"


@pytest.mark.asyncio
async def test_pipeline_error_marks_turn_degraded_and_rolls_back() -> None:
    css = _CountingCSS(raises=True)
    mgr, _ = _manager(css)
    turn = await mgr.on_final(_final())  # must NOT raise
    assert turn["degraded"] is True and turn["error"] == "pipeline_error"
    assert turn["transferred"] is False
    assert css.rolled_back is True  # Finding 2: session rolled back after the failure


@pytest.mark.asyncio
async def test_pipeline_error_rollback_failure_is_safe() -> None:
    # Even if rollback itself raises, run_turn must still return a degraded turn.
    css = _CountingCSS(raises=True, rollback_raises=True)
    svc = StreamingTurnService(css)
    turn = await svc.run_turn(call_session_id=1, stream_id=1, transcript=_final())
    assert turn["degraded"] is True and turn["error"] == "pipeline_error"
    assert css.rolled_back is True


def test_turn_dict_has_no_raw_audio() -> None:
    svc = StreamingTurnService(_CountingCSS())
    base = svc._base(_final(), text="Salom", truncated=False)
    assert not any(bad in k for k in base for bad in ("payload", "audio", "base64", "raw"))


# --- real pipeline (db_session) ---------------------------------------------
class _StubKnowledge:
    def __init__(self, chunks: list[str]) -> None:
        self._matches = [
            KBMatch(id=i + 1, title=f"item-{i + 1}", content=c, category="faq")
            for i, c in enumerate(chunks)
        ]

    async def search(self, query, language, intent=None) -> list[KBMatch]:
        return list(self._matches)


def _real_service(
    session: AsyncSession, chunks: list[str] | None = None
) -> StreamingTurnService:
    ai = AIService(provider=MockAIProvider(), knowledge=_StubKnowledge(chunks or []))
    audit = AuditLogService(session)
    operator = OperatorTransferDecisionService(
        session, MockOperatorAvailability(OperatorState.AVAILABLE), audit
    )
    css = CallSessionService(session, ai, audit, operator)
    return StreamingTurnService(css)


async def _new_call(session: AsyncSession) -> Call:
    css = CallSessionService(
        session,
        AIService(provider=MockAIProvider(), knowledge=_StubKnowledge([])),
        AuditLogService(session),
        OperatorTransferDecisionService(
            session, MockOperatorAvailability(OperatorState.AVAILABLE), AuditLogService(session)
        ),
    )
    return (await css.start_call(from_number="+998901112233", to_number="clinic")).call


@pytest.mark.asyncio
async def test_emergency_final_persists_103(db_session: AsyncSession) -> None:
    call = await _new_call(db_session)
    svc = _real_service(db_session)
    turn = await svc.run_turn(
        call_session_id=call.id, stream_id=1, transcript=_final(text="Nafas ololmayapman!"),
    )
    assert turn["action"] == "emergency"
    assert turn["transferred"] is True
    assert "103" in turn["ai_text"]
    assert turn["degraded"] is False


@pytest.mark.asyncio
async def test_unsafe_final_blocked_by_guard(db_session: AsyncSession) -> None:
    call = await _new_call(db_session)
    svc = _real_service(db_session)
    turn = await svc.run_turn(
        call_session_id=call.id, stream_id=1,
        transcript=_final(text="Menga tashxis qo'ying, nima kasallik?"),
    )
    assert turn["action"] != "allow"  # guard transferred/blocked, did not answer freely


@pytest.mark.asyncio
async def test_kb_grounded_final_persists_sources(db_session: AsyncSession) -> None:
    call = await _new_call(db_session)
    svc = _real_service(db_session, chunks=["Klinika 9:00-18:00 ishlaydi."])
    turn = await svc.run_turn(
        call_session_id=call.id, stream_id=1, transcript=_final(text="Ish vaqtingiz qanday?"),
    )
    assert turn["action"] == "allow"
    assert turn["sources"] and turn["sources"][0]["id"] == 1


@pytest.mark.asyncio
async def test_transfer_final_persists_transfer_reason(db_session: AsyncSession) -> None:
    call = await _new_call(db_session)
    svc = _real_service(db_session, chunks=[])  # empty KB -> factual question transfers
    turn = await svc.run_turn(
        call_session_id=call.id, stream_id=1,
        transcript=_final(text="Kardiolog qabuli narxi qancha?"),
    )
    assert turn["transferred"] is True
    assert turn["transfer_reason"] is not None


# --- WebSocket integration: emergency final end to end ----------------------
def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def _ws_start(stream_sid, call_sid, phrase) -> dict:
    cp = {
        "call_sid": call_sid,
        "stream_token": _WS_PROVIDER.make_stream_token(call_sid),
        "test_phrase": phrase,
    }
    return {
        "event": "start", "sequenceNumber": "1", "streamSid": stream_sid,
        "start": {
            "streamSid": stream_sid, "callSid": call_sid, "tracks": ["inbound"],
            "mediaFormat": {"encoding": "audio/x-mulaw", "sampleRate": 8000, "channels": 1},
            "customParameters": cp,
        },
    }


def _media(payload, seq="2") -> dict:
    return {"event": "media", "sequenceNumber": seq, "media": {"track": "inbound", "payload": payload}}


@pytest.fixture
def attach_spy(monkeypatch):
    calls: list[dict] = []
    orig = TelephonyStreamService.attach_streaming_summary

    async def _spy(self, stream, summary):
        calls.append(summary)
        return await orig(self, stream, summary)

    monkeypatch.setattr(TelephonyStreamService, "attach_streaming_summary", _spy)
    return calls


def test_ws_final_runs_ai_turn_and_persists_emergency(monkeypatch, attach_spy) -> None:
    import app.api.v1.telephony as tele

    monkeypatch.setattr(tele, "get_telephony_provider", lambda: _WS_PROVIDER)
    monkeypatch.setattr(settings, "twilio_use_media_streams", True)
    monkeypatch.setattr(settings, "streaming_stt_enabled", True)
    monkeypatch.setattr(settings, "streaming_stt_ai_turns_enabled", True)
    monkeypatch.setattr(settings, "streaming_stt_final_after_frames", 2)

    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    state = {"init": False}
    call_sid = "CA-emrg"

    async def _override():
        if not state["init"]:
            async with engine.begin() as conn:
                await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=_TABLES))
            # Seed a CallSession + linked TelephonyCall so the stream resolves it.
            factory0 = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
            async with factory0() as s0:
                call = await _new_call(s0)
                s0.add(TelephonyCall(
                    provider="twilio", provider_call_id=call_sid, call_session_id=call.id,
                    from_number="+998901112233", to_number="clinic", status="in_progress",
                    direction="inbound",
                ))
                await s0.commit()
            state["init"] = True
        factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _override
    client = TestClient(app)
    try:
        with client.websocket_connect(WS_URL) as ws:
            ws.send_json(_ws_start("MZ-emrg", call_sid, phrase="Nafas ololmayapman"))
            ws.send_json(_media(_b64(b"\x00" * 160)))
            ws.send_json(_media(_b64(b"\x00" * 160), seq="3"))
            ws.send_json({"event": "stop", "streamSid": "MZ-emrg", "stop": {}})
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()
    finally:
        app.dependency_overrides.clear()

    assert len(attach_spy) >= 1
    s = attach_spy[-1]
    assert s["stopped_reason"] == "stop_event"
    assert s["turn_count"] == 1
    turn = s["turns"][0]
    assert turn["transcript_text"] == "Nafas ololmayapman"
    assert turn["action"] == "emergency"
    assert turn["transferred"] is True
    assert "103" in turn["ai_text"]
    assert "payload" not in str(s) and "base64" not in str(s)


def test_ws_turn_db_error_rolls_back_and_persists_degraded(monkeypatch, attach_spy) -> None:
    """Finding 2: a DB-style failure in the pipeline rolls back the session, the
    degraded turn is still persisted, and the WebSocket does not crash."""
    import app.api.v1.telephony as tele

    monkeypatch.setattr(tele, "get_telephony_provider", lambda: _WS_PROVIDER)
    monkeypatch.setattr(settings, "twilio_use_media_streams", True)
    monkeypatch.setattr(settings, "streaming_stt_enabled", True)
    monkeypatch.setattr(settings, "streaming_stt_ai_turns_enabled", True)
    monkeypatch.setattr(settings, "streaming_stt_final_after_frames", 2)

    rb = {"n": 0}
    orig_rb = CallSessionService.rollback

    async def _spy_rollback(self):
        rb["n"] += 1
        return await orig_rb(self)  # real rollback keeps the session usable

    async def _raise(self, *, call_id, text, language=None):
        raise RuntimeError("db boom")  # transaction-style failure before commit

    monkeypatch.setattr(CallSessionService, "rollback", _spy_rollback)
    monkeypatch.setattr(CallSessionService, "handle_message", _raise)

    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    state = {"init": False}
    call_sid = "CA-dberr"

    async def _override():
        if not state["init"]:
            async with engine.begin() as conn:
                await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=_TABLES))
            factory0 = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
            async with factory0() as s0:
                call = await _new_call(s0)
                s0.add(TelephonyCall(
                    provider="twilio", provider_call_id=call_sid, call_session_id=call.id,
                    from_number="+998901112233", to_number="clinic", status="in_progress",
                    direction="inbound",
                ))
                await s0.commit()
            state["init"] = True
        factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _override
    client = TestClient(app)
    try:
        with client.websocket_connect(WS_URL) as ws:
            ws.send_json(_ws_start("MZ-dberr", call_sid, phrase="Ish vaqtingiz qanday"))
            ws.send_json(_media(_b64(b"\x00" * 160)))
            ws.send_json(_media(_b64(b"\x00" * 160), seq="3"))
            ws.send_json({"event": "stop", "streamSid": "MZ-dberr", "stop": {}})
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()
    finally:
        app.dependency_overrides.clear()

    assert rb["n"] >= 1  # session was rolled back after the failure
    assert len(attach_spy) >= 1  # summary still persisted (commit did not break)
    s = attach_spy[-1]
    assert s["stopped_reason"] == "stop_event"
    assert s["turn_count"] == 1
    assert s["turns"][0]["degraded"] is True
    assert s["turns"][0]["error"] == "pipeline_error"
