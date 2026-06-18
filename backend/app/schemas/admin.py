from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AdminCallOut(BaseModel):
    id: int
    twilio_call_sid: str
    from_number: str
    to_number: str
    language: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


class AdminStatsOut(BaseModel):
    total_calls: int
    ai_resolved: int
    operator_transfers: int
    callbacks_required: int
    kb_items: int
    recent_calls: list[AdminCallOut] = []


class TranscriptOut(BaseModel):
    id: int
    role: str
    text: str
    created_at: Optional[datetime] = None


class TransferInfo(BaseModel):
    reason: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class CallbackTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    call_session_id: int
    patient_phone: Optional[str] = None
    reason: str
    priority: str
    status: str
    due_at: Optional[datetime] = None
    notes: Optional[str] = None
    assigned_to_user_id: Optional[int] = None
    resolution_notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    rescheduled_at: Optional[datetime] = None
    last_status_changed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AuditLogOut(BaseModel):
    id: int
    event_type: str
    actor_user_id: Optional[int] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[dict] = None  # redacted
    created_at: Optional[datetime] = None


class RescheduleRequest(BaseModel):
    due_at: datetime


class CallbackNotesRequest(BaseModel):
    resolution_notes: str


class AuditEventOut(BaseModel):
    event: str
    data: Optional[dict] = None
    created_at: Optional[datetime] = None


class AdminCallDetailOut(AdminCallOut):
    transcripts: list[TranscriptOut] = []
    transfer: Optional[TransferInfo] = None
    callback: Optional[CallbackTaskOut] = None
    sources: list[dict] = []
    reason_codes: list[str] = []
    audit_events: list[AuditEventOut] = []
