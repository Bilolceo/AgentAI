"""Doctor + Appointment schemas (M2). Manager views are phone-masked + name-short."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# --- Doctor ------------------------------------------------------------------
class DoctorCreate(BaseModel):
    full_name: str
    specialty: Optional[str] = None
    room: Optional[str] = None
    working_days: Optional[str] = None
    working_hours: Optional[str] = None
    is_active: bool = True


class DoctorUpdate(BaseModel):
    full_name: Optional[str] = None
    specialty: Optional[str] = None
    room: Optional[str] = None
    working_days: Optional[str] = None
    working_hours: Optional[str] = None
    is_active: Optional[bool] = None


class DoctorOut(BaseModel):
    id: int
    full_name: str
    specialty: Optional[str] = None
    room: Optional[str] = None
    working_days: Optional[str] = None
    working_hours: Optional[str] = None
    is_active: bool


class DoctorWorkloadOut(BaseModel):
    doctor_id: int
    full_name: str
    specialty: Optional[str] = None
    appointments: int


# --- Appointment -------------------------------------------------------------
class AppointmentCreate(BaseModel):
    service: str
    doctor_id: Optional[int] = None
    call_session_id: Optional[int] = None
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: int = 30
    status: str = "pending"
    source: str = "manual"
    operator_required: bool = False
    notes: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    status: str


# Manager-safe view: short patient name + masked phone + doctor name, no raw notes.
class AppointmentManagerOut(BaseModel):
    id: int
    scheduled_at: Optional[datetime] = None
    duration_minutes: int
    patient_short: Optional[str] = None
    phone_masked: Optional[str] = None
    service: str
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    status: str
    source: str
    operator_required: bool
    has_notes: bool


# --- Public self-service booking ---------------------------------------------
class PublicServiceOut(BaseModel):
    specialty: str
    doctor_count: int


class PublicDoctorOut(BaseModel):
    id: int
    full_name: str
    specialty: Optional[str] = None
    room: Optional[str] = None


class PublicSlotsOut(BaseModel):
    doctor_id: int
    date: str
    slots: list[str]


class PublicBookingCreate(BaseModel):
    doctor_id: int
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    patient_name: str
    patient_phone: str
    service: Optional[str] = None
    notes: Optional[str] = None


class PublicBookingResult(BaseModel):
    ok: bool
    reference: str
    status: str
    doctor_name: str
    scheduled_at: Optional[datetime] = None


class ManagerReportOut(BaseModel):
    range: str
    total: int
    by_status: dict[str, int]
    ai_created: int
    operator_required: int
    cancelled: int
    no_show: int
    by_doctor: list[DoctorWorkloadOut]
