from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class IncomingCallForm(BaseModel):
    """Twilio voice webhook form-encoded maydonlari (asosiylari)."""

    CallSid: str
    From: str = ""
    To: str = ""
    CallStatus: Optional[str] = None


class TelephonyCallOut(BaseModel):
    """Telephony intake record (safe metadata only; no audio, no secrets)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    provider_call_id: Optional[str] = None
    call_session_id: Optional[int] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    status: str
    direction: str
    raw_metadata: Optional[dict] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TelephonyCallDetailOut(TelephonyCallOut):
    pass


class TelephonyStreamOut(BaseModel):
    """Twilio Media Streams record (counts only; no audio, no secrets)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    provider_call_id: Optional[str] = None
    stream_sid: Optional[str] = None
    telephony_call_id: Optional[int] = None
    status: str
    media_frames_count: int
    media_bytes_count: int
    last_sequence_number: Optional[int] = None
    stream_metadata: Optional[dict] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TelephonyStreamDetailOut(TelephonyStreamOut):
    pass
