from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CallbackTask(Base):
    """Created when a transfer is requested but no operator is available (TZ §4.6).

    The patient's number is saved and a callback obligation is recorded for an
    operator to follow up.
    """

    __tablename__ = "callback_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_session_id: Mapped[int] = mapped_column(ForeignKey("calls.id"), index=True)
    patient_phone: Mapped[Optional[str]] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(String(48))
    priority: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(24), default="callback_required")
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    # Lifecycle (A8)
    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admin_users.id"))
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rescheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_status_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
