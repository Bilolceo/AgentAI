from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    twilio_call_sid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    from_number: Mapped[str] = mapped_column(String(32))
    to_number: Mapped[str] = mapped_column(String(32))
    language: Mapped[Optional[str]] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(32), default="in_progress")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    transcripts: Mapped[list["Transcript"]] = relationship(  # noqa: F821
        back_populates="call", cascade="all, delete-orphan"
    )
