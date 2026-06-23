"""Manager dashboard endpoints (M1a) - manager-safe, role-gated.

Reuses AdminDashboardService but returns ONLY non-technical, manager-safe data
(no voice/provider/stream/latency/transcript fields). Phone numbers are masked
server-side. Gated to manager / admin / super_admin (operators are excluded).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.admin_user import AdminUser
from app.models.appointment import Appointment
from app.schemas.clinic import (
    AppointmentCreate,
    AppointmentManagerOut,
    AppointmentStatusUpdate,
    DoctorCreate,
    DoctorOut,
    DoctorUpdate,
    DoctorWorkloadOut,
    ManagerReportOut,
)
from app.schemas.manager import ManagerActionItemOut, ManagerCallOut, ManagerStatsOut
from app.services.admin.dashboard import AdminDashboardService
from app.services.auth.deps import require_roles
from app.services.clinic.service import AppointmentService, DoctorService, range_for, short_name
from app.services.voice.live_call import redact_number

router = APIRouter()

# Manager dashboard is for the clinic manager/owner; admins/super_admins also see it.
_MANAGER = require_roles("manager", "admin", "super_admin")
_SUPER = require_roles("super_admin")


def _today_start() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid date (use YYYY-MM-DD)")


def _appt_out(a: Appointment, doctor_name: Optional[str]) -> AppointmentManagerOut:
    return AppointmentManagerOut(
        id=a.id,
        scheduled_at=a.scheduled_at,
        duration_minutes=a.duration_minutes,
        patient_short=short_name(a.patient_name),
        phone_masked=redact_number(a.patient_phone) or None,
        service=a.service,
        doctor_id=a.doctor_id,
        doctor_name=doctor_name,
        status=a.status,
        source=a.source,
        operator_required=a.operator_required,
        has_notes=bool(a.notes),
    )

# Callback statuses that still need manager/operator attention.
_OPEN_CALLBACK = ("callback_required", "assigned")


def _mask_phone(raw: Optional[str]) -> Optional[str]:
    """Mask a phone for manager display (reuses the shared redact_number helper)."""
    masked = redact_number(raw)
    return masked or None


@router.get("/stats", response_model=ManagerStatsOut)
async def manager_stats(
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_MANAGER),
) -> ManagerStatsOut:
    s = await AdminDashboardService(session).stats()
    return ManagerStatsOut(
        total_calls=s["total_calls"],
        ai_resolved=s["ai_resolved"],
        operator_transfers=s["operator_transfers"],
        callbacks_required=s["callbacks_required"],
        kb_items=s["kb_items"],
    )


@router.get("/action-items", response_model=list[ManagerActionItemOut])
async def manager_action_items(
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_MANAGER),
) -> list[ManagerActionItemOut]:
    rows = await AdminDashboardService(session).list_callbacks(limit=100)
    return [
        ManagerActionItemOut(
            id=r["id"],
            call_session_id=r["call_session_id"],
            reason=r["reason"],
            priority=r["priority"],
            status=r["status"],
            due_at=r["due_at"],
            phone_masked=_mask_phone(r["patient_phone"]),
            created_at=r["created_at"],
        )
        for r in rows
        if r["status"] in _OPEN_CALLBACK
    ]


@router.get("/recent-calls", response_model=list[ManagerCallOut])
async def manager_recent_calls(
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_MANAGER),
) -> list[ManagerCallOut]:
    capped = max(1, min(limit, 50))
    rows = await AdminDashboardService(session).list_calls(limit=capped)
    return [
        ManagerCallOut(
            id=r["id"],
            from_masked=_mask_phone(r["from_number"]),
            language=r["language"],
            status=r["status"],
            started_at=r["started_at"],
            duration_seconds=r["duration_seconds"],
        )
        for r in rows
    ]


# --- M2: schedule / doctors / reports ---------------------------------------
@router.get("/schedule", response_model=list[AppointmentManagerOut])
async def manager_schedule(
    date: Optional[str] = None,
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_MANAGER),
) -> list[AppointmentManagerOut]:
    appts_svc = AppointmentService(session)
    doctors = {d.id: d.full_name for d in await DoctorService(session).list()}
    if date_from or date_to:
        start = _parse_date(date_from) or _today_start()
        end = (_parse_date(date_to) or start) + timedelta(days=1)
        appts = await appts_svc.list_range(start, end)
    else:
        appts = await appts_svc.list_day(_parse_date(date) or datetime.now(timezone.utc))
    return [_appt_out(a, doctors.get(a.doctor_id) if a.doctor_id else None) for a in appts]


@router.get("/doctors", response_model=list[DoctorWorkloadOut])
async def manager_doctors(
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_MANAGER),
) -> list[DoctorWorkloadOut]:
    docs = await DoctorService(session).list()
    start = _today_start()
    workload = await AppointmentService(session).doctor_workload(start, start + timedelta(days=1))
    return [
        DoctorWorkloadOut(
            doctor_id=d.id, full_name=d.full_name, specialty=d.specialty,
            appointments=workload.get(d.id, 0),
        )
        for d in docs
    ]


@router.get("/reports", response_model=ManagerReportOut)
async def manager_reports(
    period: str = Query("today", alias="range"),
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_MANAGER),
) -> ManagerReportOut:
    period = period if period in ("today", "week", "month") else "today"
    start, end = range_for(period)
    appts_svc = AppointmentService(session)
    rep = await appts_svc.report(start, end)
    workload = await appts_svc.doctor_workload(start, end)
    docs = {d.id: d for d in await DoctorService(session).list()}
    by_doctor = [
        DoctorWorkloadOut(
            doctor_id=did,
            full_name=docs[did].full_name if did in docs else str(did),
            specialty=docs[did].specialty if did in docs else None,
            appointments=n,
        )
        for did, n in workload.items()
    ]
    return ManagerReportOut(range=period, by_doctor=by_doctor, **rep)


# --- M2: doctor / appointment management (manager-gated) --------------------
@router.post("/doctors", response_model=DoctorOut, status_code=201)
async def create_doctor(
    payload: DoctorCreate,
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_MANAGER),
) -> DoctorOut:
    doctor = await DoctorService(session).create(**payload.model_dump())
    await session.commit()
    return DoctorOut.model_validate(doctor, from_attributes=True)


@router.patch("/doctors/{doctor_id}", response_model=DoctorOut)
async def update_doctor(
    doctor_id: int,
    payload: DoctorUpdate,
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_MANAGER),
) -> DoctorOut:
    doctor = await DoctorService(session).update(doctor_id, **payload.model_dump(exclude_unset=True))
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    await session.commit()
    return DoctorOut.model_validate(doctor, from_attributes=True)


@router.post("/appointments", response_model=AppointmentManagerOut, status_code=201)
async def create_appointment(
    payload: AppointmentCreate,
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_MANAGER),
) -> AppointmentManagerOut:
    try:
        appt = await AppointmentService(session).create(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await session.commit()
    doctor = await DoctorService(session).get(appt.doctor_id) if appt.doctor_id else None
    return _appt_out(appt, doctor.full_name if doctor else None)


@router.patch("/appointments/{appt_id}/status", response_model=AppointmentManagerOut)
async def set_appointment_status(
    appt_id: int,
    payload: AppointmentStatusUpdate,
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_MANAGER),
) -> AppointmentManagerOut:
    try:
        appt = await AppointmentService(session).set_status(appt_id, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    await session.commit()
    doctor = await DoctorService(session).get(appt.doctor_id) if appt.doctor_id else None
    return _appt_out(appt, doctor.full_name if doctor else None)


@router.post("/seed-demo")
async def seed_demo(
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_SUPER),
) -> dict:
    """Seed SYNTHETIC demo doctors + today's appointments (super_admin, idempotent).

    Names are fake placeholders for the demo - never real patient data."""
    doc_svc = DoctorService(session)
    if await doc_svc.list():
        return {"seeded": False}
    d1 = await doc_svc.create(full_name="Karimov Bobur", specialty="urolog",
                              room="101", working_days="mon,tue,wed,thu,fri", working_hours="09:00-18:00")
    d2 = await doc_svc.create(full_name="Rustamov Sardor", specialty="urolog",
                              room="102", working_days="mon,tue,wed,thu,fri", working_hours="10:00-17:00")
    appt_svc = AppointmentService(session)
    base = _today_start().replace(hour=9)
    demo = [
        (d1.id, 0, "Aliyev Akmal", "+998901112233", "Urolog konsultatsiyasi", "confirmed", "ai_call"),
        (d1.id, 30, "Xasanova Madina", "+998901112244", "UZI", "pending", "operator"),
        (d1.id, 60, "Tursunov Jasur", "+998901112255", "Tahlil", "new", "ai_call"),
        (d2.id, 30, "Yusupova Dilnoza", "+998901112266", "Qayta ko'rik", "confirmed", "manual"),
        (d2.id, 90, "Olimov Rustam", "+998901112277", "Konsultatsiya", "cancelled", "ai_call"),
    ]
    for doc_id, offset_min, name, phone, service, status, source in demo:
        await appt_svc.create(
            doctor_id=doc_id, patient_name=name, patient_phone=phone, service=service,
            scheduled_at=base + timedelta(minutes=offset_min), status=status, source=source,
        )
    await session.commit()
    return {"seeded": True, "doctors": 2, "appointments": len(demo)}
