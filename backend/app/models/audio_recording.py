from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AudioRecording(Base):
    """Metadata for audio stored OUTSIDE the database (object storage / local disk).

    Created by the voice pipeline for inbound caller audio (with STT transcript
    metadata) and outbound synthesized TTS audio. No raw audio blob is stored
    here -- only the storage key + checksum + safe metadata.
    """

    __tablename__ = "audio_recordings"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_session_id: Mapped[int] = mapped_column(ForeignKey("calls.id"), index=True)
    call_message_id: Mapped[Optional[int]] = mapped_column(ForeignKey("transcripts.id"))

    direction: Mapped[str] = mapped_column(String(16))  # inbound | outbound
    kind: Mapped[str] = mapped_column(String(24))  # user_audio | ai_tts | full_call | system

    storage_provider: Mapped[str] = mapped_column(String(24))
    storage_key: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    checksum_sha256: Mapped[str] = mapped_column(String(64))

    transcript_text: Mapped[Optional[str]] = mapped_column(Text)
    transcript_language: Mapped[Optional[str]] = mapped_column(String(16))
    transcript_confidence: Mapped[Optional[float]] = mapped_column(Float)

    tts_voice: Mapped[Optional[str]] = mapped_column(String(64))
    tts_text: Mapped[Optional[str]] = mapped_column(Text)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
