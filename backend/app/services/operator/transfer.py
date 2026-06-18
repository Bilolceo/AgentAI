"""Operator Transfer Decision Engine (TZ §4.6) — backend only.

Decides priority/status for an escalation, updates the call-session status,
creates a callback task when no operator is available, and records an audit
event. Real SIP/Twilio call bridging is NOT implemented here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.call import Call
from app.models.callback_task import CallbackTask
from app.services.audit.log import AuditEvent, AuditLogService
from app.services.operator.availability import (
    OperatorAvailabilityProvider,
    OperatorState,
)
from app.services.safety.guard import ReasonCode

log = get_logger("operator")


class TransferReason(str, Enum):
    EXPLICIT_OPERATOR_REQUEST = "explicit_operator_request"
    MEDICAL_ADVICE_RISK = "medical_advice_risk"
    COMPLAINT = "complaint"
    LOW_CONFIDENCE = "low_confidence"
    UNCLEAR_PRICE_OR_SCHEDULE = "unclear_price_or_schedule"
    EMERGENCY = "emergency"
    ANGRY_OR_AGGRESSIVE_USER = "angry_or_aggressive_user"
    OPERATOR_BUSY_CALLBACK = "operator_busy_callback"
    UNSAFE_AI_OUTPUT = "unsafe_ai_output"


class TransferPriority(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TransferStatus(str, Enum):
    REQUESTED = "requested"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    CALLBACK_REQUIRED = "callback_required"
    CANCELLED = "cancelled"


# Map the safety guard / AI result reason codes onto transfer reasons.
_GUARD_TO_TRANSFER: dict[ReasonCode, TransferReason] = {
    ReasonCode.OPERATOR_REQUEST: TransferReason.EXPLICIT_OPERATOR_REQUEST,
    ReasonCode.DIAGNOSIS: TransferReason.MEDICAL_ADVICE_RISK,
    ReasonCode.MEDICINE: TransferReason.MEDICAL_ADVICE_RISK,
    ReasonCode.DOSAGE: TransferReason.MEDICAL_ADVICE_RISK,
    ReasonCode.TREATMENT: TransferReason.MEDICAL_ADVICE_RISK,
    ReasonCode.DATA_DISCLOSURE: TransferReason.MEDICAL_ADVICE_RISK,
    ReasonCode.COMPLAINT: TransferReason.COMPLAINT,
    ReasonCode.ANGRY: TransferReason.ANGRY_OR_AGGRESSIVE_USER,
    ReasonCode.PRICE_OR_SCHEDULE_UNCLEAR: TransferReason.UNCLEAR_PRICE_OR_SCHEDULE,
    ReasonCode.LOW_CONFIDENCE: TransferReason.LOW_CONFIDENCE,
    ReasonCode.EMERGENCY: TransferReason.EMERGENCY,
    ReasonCode.UNSAFE_OUTPUT: TransferReason.UNSAFE_AI_OUTPUT,
}

# Priority per reason (TZ §4.6 rules; unspecified ones default sensibly).
_PRIORITY: dict[TransferReason, TransferPriority] = {
    TransferReason.EMERGENCY: TransferPriority.URGENT,
    TransferReason.COMPLAINT: TransferPriority.HIGH,
    TransferReason.ANGRY_OR_AGGRESSIVE_USER: TransferPriority.HIGH,
    TransferReason.UNSAFE_AI_OUTPUT: TransferPriority.HIGH,
    TransferReason.MEDICAL_ADVICE_RISK: TransferPriority.HIGH,
    TransferReason.EXPLICIT_OPERATOR_REQUEST: TransferPriority.NORMAL,
    TransferReason.LOW_CONFIDENCE: TransferPriority.NORMAL,
    TransferReason.UNCLEAR_PRICE_OR_SCHEDULE: TransferPriority.NORMAL,
    TransferReason.OPERATOR_BUSY_CALLBACK: TransferPriority.NORMAL,
}

# How soon a callback is due, by priority.
_CALLBACK_DUE_MINUTES: dict[TransferPriority, int] = {
    TransferPriority.URGENT: 5,
    TransferPriority.HIGH: 30,
    TransferPriority.NORMAL: 120,
}


def map_reason_code(reason_code: ReasonCode) -> TransferReason:
    """Map an AI/guard reason code to a transfer reason."""
    return _GUARD_TO_TRANSFER.get(reason_code, TransferReason.MEDICAL_ADVICE_RISK)


@dataclass
class TransferDecision:
    reason: TransferReason
    priority: TransferPriority
    status: TransferStatus
    callback_task_id: Optional[int] = None

    @property
    def callback_required(self) -> bool:
        return self.status is TransferStatus.CALLBACK_REQUIRED


class OperatorTransferDecisionService:
    def __init__(
        self,
        session: AsyncSession,
        availability: OperatorAvailabilityProvider,
        audit: AuditLogService,
    ) -> None:
        self._session = session
        self._availability = availability
        self._audit = audit

    async def request_transfer(
        self,
        call: Call,
        *,
        reason: TransferReason,
        patient_phone: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> TransferDecision:
        priority = _PRIORITY[reason]
        state = await self._availability.get_state()

        # Call-session status update (TZ §4.6).
        call.status = "transferred"

        callback_task_id: Optional[int] = None
        if state is OperatorState.AVAILABLE:
            status = TransferStatus.REQUESTED
        else:
            # Operator busy/unavailable → save the number, create a callback task.
            status = TransferStatus.CALLBACK_REQUIRED
            task = CallbackTask(
                call_session_id=call.id,
                patient_phone=patient_phone,
                reason=reason.value,
                priority=priority.value,
                status=status.value,
                due_at=self._due_at(priority),
                notes=notes,
            )
            self._session.add(task)
            await self._session.flush()
            callback_task_id = task.id

        await self._session.flush()

        await self._audit.record(
            AuditEvent.OPERATOR_TRANSFER_REQUESTED,
            call_id=call.id,
            data={
                "reason": reason.value,
                "priority": priority.value,
                "status": status.value,
                "operator_state": state.value,
                "callback_task_id": callback_task_id,
            },
        )
        if callback_task_id is not None:
            await self._audit.record(
                AuditEvent.CALLBACK_CREATED,
                call_id=call.id,
                data={"callback_task_id": callback_task_id, "reason": reason.value},
            )

        log.info(
            "operator_transfer",
            call_id=call.id,
            reason=reason.value,
            priority=priority.value,
            status=status.value,
        )
        return TransferDecision(reason, priority, status, callback_task_id)

    @staticmethod
    def _due_at(priority: TransferPriority) -> datetime:
        minutes = _CALLBACK_DUE_MINUTES[priority]
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)
