from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[int] = mapped_column(ForeignKey("calls.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user / assistant
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    call: Mapped["Call"] = relationship(back_populates="transcripts")  # noqa: F821
