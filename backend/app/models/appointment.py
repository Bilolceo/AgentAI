from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Status workflow (string column, validated in the service layer):
# new | pending | confirmed | arrived | in_progress | completed | cancelled | no_show | operator_required
# Source: ai_call | operator | manual
APPOINTMENT_STATUSES = (
    "new", "pending", "confirmed", "arrived", "in_progress",
    "completed", "cancelled", "no_show", "operator_required",
)
APPOINTMENT_SOURCES = ("ai_call", "operator", "manual")


class Appointment(Base):
    """A clinic appointment for the manager schedule (M2).

    Patient identity is kept minimal (display name + phone); phone is masked at
    the API layer for manager views. Optionally links to the AI call session.
    """

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("doctors.id"), index=True)
    call_session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("calls.id"))

    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    patient_phone: Mapped[Optional[str]] = mapped_column(String(32))
    service: Mapped[str] = mapped_column(String(255))

    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)

    status: Mapped[str] = mapped_column(String(24), default="pending")
    source: Mapped[str] = mapped_column(String(16), default="manual")
    operator_required: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
