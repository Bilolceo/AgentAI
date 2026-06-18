from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TranscriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    text: str
    created_at: datetime


class CallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    twilio_call_sid: str
    from_number: str
    to_number: str
    language: Optional[str]
    status: str
    started_at: datetime
    ended_at: Optional[datetime]


class CallDetailOut(CallOut):
    transcripts: list[TranscriptOut] = []
