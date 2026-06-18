"""Operator Transfer Decision Engine tests (TZ §4.6), backend only."""
from __future__ import annotations

import inspect

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.call import Call
from app.models.callback_task import CallbackTask
from app.services.audit.log import AuditLogService
from app.services.operator.availability import MockOperatorAvailability, OperatorState
from app.services.operator.transfer import (
    OperatorTransferDecisionService,
    TransferPriority,
    TransferReason,
    TransferStatus,
    map_reason_code,
)
from app.services.safety.guard import ReasonCode

# Reuse the call-session test helper for end-to-end checks.
from app.tests.test_call_session import make_service


async def _make_call(session: AsyncSession) -> Call:
    call = Call(
        twilio_call_sid="sim-xyz",
        from_number="+998901112233",
        to_number="clinic",
        status="in_progress",
    )
    session.add(call)
    await session.flush()
    return call


def _engine(
    session: AsyncSession, state: OperatorState = OperatorState.AVAILABLE
) -> OperatorTransferDecisionService:
    return OperatorTransferDecisionService(
        session, MockOperatorAvailability(state), AuditLogService(session)
    )


async def _callback_count(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(CallbackTask))


# === All TZ §4.6 transfer reasons, operator available ========================
@pytest.mark.parametrize(
    "reason,expected_priority",
    [
        (TransferReason.EXPLICIT_OPERATOR_REQUEST, TransferPriority.NORMAL),
        (TransferReason.MEDICAL_ADVICE_RISK, TransferPriority.HIGH),
        (TransferReason.COMPLAINT, TransferPriority.HIGH),
        (TransferReason.LOW_CONFIDENCE, TransferPriority.NORMAL),
        (TransferReason.UNCLEAR_PRICE_OR_SCHEDULE, TransferPriority.NORMAL),
        (TransferReason.EMERGENCY, TransferPriority.URGENT),
        (TransferReason.ANGRY_OR_AGGRESSIVE_USER, TransferPriority.HIGH),
        (TransferReason.UNSAFE_AI_OUTPUT, TransferPriority.HIGH),
    ],
)
@pytest.mark.asyncio
async def test_transfer_reason_priority_when_available(
    db_session: AsyncSession,
    reason: TransferReason,
    expected_priority: TransferPriority,
) -> None:
    call = await _make_call(db_session)
    decision = await _engine(db_session).request_transfer(
        call, reason=reason, patient_phone=call.from_number
    )
    assert decision.reason is reason
    assert decision.priority is expected_priority
    assert decision.status is TransferStatus.REQUESTED
    assert decision.callback_required is False
    assert decision.callback_task_id is None
    assert call.status == "transferred"
    assert await _callback_count(db_session) == 0


# === Operator busy / unavailable → callback task (TZ §4.6) ===================
@pytest.mark.asyncio
async def test_operator_busy_creates_callback_task(db_session: AsyncSession) -> None:
    call = await _make_call(db_session)
    decision = await _engine(db_session, OperatorState.BUSY).request_transfer(
        call, reason=TransferReason.COMPLAINT, patient_phone=call.from_number, notes="urgent"
    )
    assert decision.status is TransferStatus.CALLBACK_REQUIRED
    assert decision.callback_required is True
    assert decision.callback_task_id is not None

    task = await db_session.scalar(
        select(CallbackTask).where(CallbackTask.id == decision.callback_task_id)
    )
    assert task is not None
    assert task.call_session_id == call.id
    assert task.patient_phone == "+998901112233"
    assert task.reason == "complaint"
    assert task.priority == "high"
    assert task.status == "callback_required"
    assert task.due_at is not None
    assert task.notes == "urgent"


@pytest.mark.asyncio
async def test_operator_unavailable_creates_callback_task(db_session: AsyncSession) -> None:
    call = await _make_call(db_session)
    decision = await _engine(db_session, OperatorState.UNAVAILABLE).request_transfer(
        call, reason=TransferReason.EXPLICIT_OPERATOR_REQUEST
    )
    assert decision.status is TransferStatus.CALLBACK_REQUIRED
    assert await _callback_count(db_session) == 1


# === Audit events ============================================================
@pytest.mark.asyncio
async def test_transfer_records_audit_event(db_session: AsyncSession) -> None:
    call = await _make_call(db_session)
    await _engine(db_session).request_transfer(call, reason=TransferReason.COMPLAINT)
    events = set(
        (await db_session.scalars(select(AuditLog.event).where(AuditLog.call_id == call.id))).all()
    )
    assert "operator_transfer_requested" in events


@pytest.mark.asyncio
async def test_callback_records_callback_created_audit(db_session: AsyncSession) -> None:
    call = await _make_call(db_session)
    await _engine(db_session, OperatorState.BUSY).request_transfer(
        call, reason=TransferReason.COMPLAINT
    )
    events = set(
        (await db_session.scalars(select(AuditLog.event).where(AuditLog.call_id == call.id))).all()
    )
    assert "operator_transfer_requested" in events
    assert "callback_created" in events


# === Reason-code mapping =====================================================
@pytest.mark.parametrize(
    "code,expected",
    [
        (ReasonCode.OPERATOR_REQUEST, TransferReason.EXPLICIT_OPERATOR_REQUEST),
        (ReasonCode.MEDICINE, TransferReason.MEDICAL_ADVICE_RISK),
        (ReasonCode.DIAGNOSIS, TransferReason.MEDICAL_ADVICE_RISK),
        (ReasonCode.DOSAGE, TransferReason.MEDICAL_ADVICE_RISK),
        (ReasonCode.TREATMENT, TransferReason.MEDICAL_ADVICE_RISK),
        (ReasonCode.DATA_DISCLOSURE, TransferReason.MEDICAL_ADVICE_RISK),
        (ReasonCode.COMPLAINT, TransferReason.COMPLAINT),
        (ReasonCode.ANGRY, TransferReason.ANGRY_OR_AGGRESSIVE_USER),
        (ReasonCode.PRICE_OR_SCHEDULE_UNCLEAR, TransferReason.UNCLEAR_PRICE_OR_SCHEDULE),
        (ReasonCode.LOW_CONFIDENCE, TransferReason.LOW_CONFIDENCE),
        (ReasonCode.EMERGENCY, TransferReason.EMERGENCY),
        (ReasonCode.UNSAFE_OUTPUT, TransferReason.UNSAFE_AI_OUTPUT),
    ],
)
def test_map_reason_code(code: ReasonCode, expected: TransferReason) -> None:
    assert map_reason_code(code) is expected


# === CallSessionService integration ==========================================
@pytest.mark.asyncio
async def test_session_emergency_transfer_fields(db_session: AsyncSession) -> None:
    svc = make_service(db_session)
    call = (await svc.start_call(from_number="+998901112233", to_number="clinic")).call
    outcome = await svc.handle_message(call_id=call.id, text="Nafas ololmayapman!")
    assert outcome.transferred is True
    assert outcome.action == "emergency"
    assert outcome.reason_code == "emergency"
    assert outcome.transfer_reason == "emergency"
    assert outcome.priority == "urgent"
    assert outcome.transfer_status == "requested"
    assert outcome.callback_required is False


@pytest.mark.asyncio
async def test_session_explicit_operator_request(db_session: AsyncSession) -> None:
    svc = make_service(db_session)
    call = (await svc.start_call(from_number="+998901112233", to_number="clinic")).call
    outcome = await svc.handle_message(call_id=call.id, text="Operatorga ulang iltimos")
    assert outcome.action == "transfer"
    assert outcome.reason_code == "operator_request"
    assert outcome.transfer_reason == "explicit_operator_request"
    assert outcome.priority == "normal"


@pytest.mark.asyncio
async def test_session_busy_operator_creates_callback(db_session: AsyncSession) -> None:
    svc = make_service(db_session, operator_state=OperatorState.BUSY)
    call = (await svc.start_call(from_number="+998901112233", to_number="clinic")).call
    outcome = await svc.handle_message(call_id=call.id, text="Shikoyat qilmoqchiman")
    assert outcome.transferred is True
    assert outcome.callback_required is True
    assert outcome.transfer_status == "callback_required"
    assert await _callback_count(db_session) == 1


# === Route handlers contain no transfer business logic =======================
def test_route_handler_has_no_transfer_business_logic() -> None:
    from app.api.v1 import simulation as sim_module

    src = inspect.getsource(sim_module)
    forbidden = [
        "OperatorTransferDecisionService",
        "TransferPriority",
        "TransferStatus",
        "CallbackTask",
        "OperatorAvailability",
        "request_transfer",
        "map_reason_code",
        "get_state",
    ]
    for token in forbidden:
        assert token not in src, f"route module must not contain transfer logic: {token}"
    # It must delegate to the service.
    assert "handle_message" in src
