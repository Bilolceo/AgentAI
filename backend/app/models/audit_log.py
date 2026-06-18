from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AuditLog(Base):
    """Append-only audit trail for important actions.

    Events: call_started, language_detected, ai_response_generated,
    safety_guard_triggered, operator_transfer_requested, booking_created,
    reminder_scheduled, admin_action.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    event: Mapped[str] = mapped_column(String(64), index=True)
    call_id: Mapped[Optional[int]] = mapped_column(index=True)
    actor: Mapped[str] = mapped_column(String(64), default="system")
    actor_user_id: Mapped[Optional[int]] = mapped_column(index=True)
    data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
