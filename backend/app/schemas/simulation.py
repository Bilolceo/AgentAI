from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class StartCallRequest(BaseModel):
    from_number: str = Field(..., min_length=3, max_length=32)
    to_number: str = Field(default="clinic", max_length=32)
    language: Optional[str] = None  # "uz" | "ru"; omitted → bilingual greeting


class StartCallResponse(BaseModel):
    call_id: int
    greeting: str
    language: str  # uz | ru | unknown


class MessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    language: Optional[str] = None  # "uz-UZ" | "ru-RU"; auto-detected if omitted


class MessageResponse(BaseModel):
    reply: str
    action: str            # allow | safe_reply | transfer | emergency
    reason_code: str
    transferred: bool
    language: str
    transfer_reason: Optional[str] = None  # TZ §4.6 transfer reason
    priority: Optional[str] = None         # normal | high | urgent
    transfer_status: Optional[str] = None  # requested | callback_required | ...
    callback_required: bool = False
    sources: list = []                     # KB sources used: [{id, title}]
