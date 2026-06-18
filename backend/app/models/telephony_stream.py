from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TelephonyStream(Base):
    """Twilio Media Streams lifecycle record (WebSocket spike).

    Tracks a single media stream: counts frames/bytes only. NO raw audio payload
    is stored here (or logged anywhere). `stream_metadata` keeps a SAFE subset of
    the start event (tracks + media format), never customParameters/secrets.
    """

    __tablename__ = "telephony_streams"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(24), default="twilio", index=True)
    provider_call_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    stream_sid: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    telephony_call_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("telephony_calls.id"), index=True
    )

    status: Mapped[str] = mapped_column(String(24), default="active")  # active|stopped
    media_frames_count: Mapped[int] = mapped_column(Integer, default=0)
    media_bytes_count: Mapped[int] = mapped_column(BigInteger, default=0)
    last_sequence_number: Mapped[Optional[int]] = mapped_column(Integer)

    stream_metadata: Mapped[Optional[dict]] = mapped_column(JSON)  # safe subset only

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
