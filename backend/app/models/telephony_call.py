from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TelephonyCall(Base):
    """Telephony intake record (spike).

    Links a provider-side call (mock or Twilio) to an internal CallSession. The
    provider's raw payload is stored as a SAFE subset only (no secrets/signatures).
    This is intake metadata, not media: no audio blob lives here.
    """

    __tablename__ = "telephony_calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(24), index=True)  # mock | twilio
    provider_call_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    call_session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("calls.id"), index=True)

    from_number: Mapped[Optional[str]] = mapped_column(String(32))
    to_number: Mapped[Optional[str]] = mapped_column(String(32))

    status: Mapped[str] = mapped_column(String(24), default="received")  # received|processed|failed
    direction: Mapped[str] = mapped_column(String(16), default="inbound")  # inbound|outbound

    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSON)  # safe subset only

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
