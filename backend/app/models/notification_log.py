from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Kinds of patient-facing notifications tied to an appointment lifecycle.
NOTIFICATION_KINDS = ("booking_received", "confirmed", "cancelled", "reminder")
# Dispatch outcome: mock = logged only (no real send); sent / failed for real channels.
NOTIFICATION_STATUSES = ("mock", "sent", "failed")


class NotificationLog(Base):
    """Audit trail of outbound SMS/notifications (one row per dispatch attempt)."""

    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("appointments.id", ondelete="SET NULL"), index=True
    )
    to_phone: Mapped[str] = mapped_column(String(32))
    channel: Mapped[str] = mapped_column(String(16))  # mock | twilio | eskiz
    kind: Mapped[str] = mapped_column(String(32))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="mock")
    provider_ref: Mapped[Optional[str]] = mapped_column(String(128))
    error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
