from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Doctor(Base):
    """A clinic doctor (urologist etc.) for the manager schedule + workload (M2)."""

    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    specialty: Mapped[Optional[str]] = mapped_column(String(64))  # e.g. urolog
    room: Mapped[Optional[str]] = mapped_column(String(64))  # room / branch
    working_days: Mapped[Optional[str]] = mapped_column(String(64))  # "mon,tue,wed,thu,fri"
    working_hours: Mapped[Optional[str]] = mapped_column(String(64))  # "09:00-18:00"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
