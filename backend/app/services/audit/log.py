"""AuditLogService — records important actions to an append-only table."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.audit_log import AuditLog

log = get_logger("audit")

# Substrings that mark a metadata key as sensitive (value is redacted on read).
_SENSITIVE_KEY_PARTS = ("password", "secret", "token", "recovery", "totp", "hash")
_REDACTED = "[REDACTED]"


def redact_metadata(data: Optional[dict]) -> Optional[dict]:
    if not data:
        return data
    out: dict = {}
    for key, value in data.items():
        out[key] = _REDACTED if any(p in key.lower() for p in _SENSITIVE_KEY_PARTS) else value
    return out


class AuditEvent(str, Enum):
    CALL_STARTED = "call_started"
    LANGUAGE_DETECTED = "language_detected"
    AI_RESPONSE_GENERATED = "ai_response_generated"
    SAFETY_GUARD_TRIGGERED = "safety_guard_triggered"
    OPERATOR_TRANSFER_REQUESTED = "operator_transfer_requested"
    CALLBACK_CREATED = "callback_created"
    BOOKING_CREATED = "booking_created"
    REMINDER_SCHEDULED = "reminder_scheduled"
    ADMIN_ACTION = "admin_action"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_2FA_REQUIRED = "login_2fa_required"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    USER_PASSWORD_RESET = "user_password_reset"
    USER_2FA_RESET = "user_2fa_reset"
    PASSWORD_CHANGE_SUCCESS = "password_change_success"
    AUTH_LOCKED = "auth_locked"
    WEAK_PASSWORD_REJECTED = "weak_password_rejected"
    KNOWLEDGE_ITEM_CREATED = "knowledge_item_created"
    KNOWLEDGE_ITEM_UPDATED = "knowledge_item_updated"
    KNOWLEDGE_ITEM_DELETED = "knowledge_item_deleted"
    KNOWLEDGE_ITEM_ACTIVATED = "knowledge_item_activated"
    KNOWLEDGE_ITEM_DEACTIVATED = "knowledge_item_deactivated"
    CALLBACK_ASSIGNED = "callback_assigned"
    CALLBACK_COMPLETED = "callback_completed"
    CALLBACK_CANCELLED = "callback_cancelled"
    CALLBACK_RESCHEDULED = "callback_rescheduled"
    CALLBACK_NOTES_UPDATED = "callback_notes_updated"
    AUDIO_RECORDING_DELETED = "audio_recording_deleted"
    TELEPHONY_CALL_STARTED = "telephony_call_started"
    TELEPHONY_CALL_PROCESSED = "telephony_call_processed"


class AuditLogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        event: AuditEvent,
        *,
        call_id: int | None = None,
        actor: str = "system",
        actor_user_id: int | None = None,
        data: dict | None = None,
    ) -> None:
        self._session.add(
            AuditLog(
                event=event.value,
                call_id=call_id,
                actor=actor,
                actor_user_id=actor_user_id,
                data=data,
            )
        )
        await self._session.flush()
        log.info("audit_recorded", audit_event=event.value, call_id=call_id, actor=actor)

    async def list_logs(
        self,
        *,
        event_type: Optional[str] = None,
        actor_user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Newest-first audit logs with optional filters and pagination."""
        stmt = select(AuditLog)
        if event_type:
            stmt = stmt.where(AuditLog.event == event_type)
        if actor_user_id is not None:
            stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
        if date_from is not None:
            stmt = stmt.where(AuditLog.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(AuditLog.created_at <= date_to)
        stmt = stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        stmt = stmt.limit(max(1, min(limit, 200))).offset(max(0, offset))
        return list((await self._session.execute(stmt)).scalars())
