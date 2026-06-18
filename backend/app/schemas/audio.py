"""Admin schemas for audio recording metadata (no raw audio bytes)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AudioRecordingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    call_session_id: int
    call_message_id: Optional[int] = None
    direction: str
    kind: str
    storage_provider: str
    storage_key: str
    content_type: str
    size_bytes: int
    duration_ms: Optional[int] = None
    checksum_sha256: str
    transcript_text: Optional[str] = None
    transcript_language: Optional[str] = None
    transcript_confidence: Optional[float] = None
    tts_voice: Optional[str] = None
    tts_text: Optional[str] = None
    is_deleted: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AudioRecordingDetailOut(AudioRecordingOut):
    # Placeholder signed URL (mock storage). None if not resolvable.
    signed_url: Optional[str] = None
