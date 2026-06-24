"""Public self-service booking (customer-facing, no auth).

Customers pick a direction (specialty) -> doctor -> free slot, then submit a
booking request. Requests are created as `pending` (source=web) and must be
confirmed by an operator/manager. The surface is intentionally minimal: it only
exposes doctors' public info and free slots, never other patients' data.

Anti-abuse: a small in-memory per-IP rate limit plus a per-phone active-request
cap in the service layer. Phone/name are validated and normalized server-side.
"""
from __future__ import annotations

import time as _time
from collections import deque
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.schemas.clinic import (
    PublicBookingCreate,
    PublicBookingResult,
    PublicDoctorOut,
    PublicServiceOut,
    PublicSlotsOut,
)
from app.services.clinic.booking import BookingError, PublicBookingService, parse_date
from app.services.notifications.appointment_sms import notify_appointment

router = APIRouter()

# Simple in-memory sliding-window rate limit per client IP for the write path.
_RATE_WINDOW_SEC = 600  # 10 minutes
_RATE_MAX = 5
_hits: dict[str, deque[float]] = {}


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate(ip: str) -> None:
    now = _time.monotonic()
    dq = _hits.setdefault(ip, deque())
    while dq and now - dq[0] > _RATE_WINDOW_SEC:
        dq.popleft()
    if len(dq) >= _RATE_MAX:
        raise HTTPException(status_code=429, detail="rate_limited")
    dq.append(now)


@router.get("/services", response_model=list[PublicServiceOut])
async def public_services(session: AsyncSession = Depends(get_session)):
    return await PublicBookingService(session).services()


@router.get("/doctors", response_model=list[PublicDoctorOut])
async def public_doctors(
    specialty: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    docs = await PublicBookingService(session).doctors(specialty)
    return [
        PublicDoctorOut(id=d.id, full_name=d.full_name, specialty=d.specialty, room=d.room)
        for d in docs
    ]


@router.get("/slots", response_model=PublicSlotsOut)
async def public_slots(
    doctor_id: int = Query(...),
    date: str = Query(..., description="YYYY-MM-DD"),
    session: AsyncSession = Depends(get_session),
):
    svc = PublicBookingService(session)
    doctor = next((d for d in await svc.doctors() if d.id == doctor_id), None)
    if doctor is None:
        raise HTTPException(status_code=404, detail="doctor_not_found")
    try:
        slots = await svc.available_slots(doctor, parse_date(date))
    except BookingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PublicSlotsOut(doctor_id=doctor_id, date=date, slots=slots)


@router.post("/appointments", response_model=PublicBookingResult)
async def public_book(
    payload: PublicBookingCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    _check_rate(_client_ip(request))
    svc = PublicBookingService(session)
    try:
        appt = await svc.book(
            doctor_id=payload.doctor_id,
            date=payload.date,
            time_hhmm=payload.time,
            patient_name=payload.patient_name,
            patient_phone=payload.patient_phone,
            service=payload.service,
            notes=payload.notes,
        )
    except BookingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    doctor = await svc.doctors()
    doctor_name = next((d.full_name for d in doctor if d.id == appt.doctor_id), "")
    # Confirmation that the request was received (best-effort; mock by default).
    await notify_appointment(session, appt, "booking_received", doctor_name=doctor_name)
    await session.commit()
    return PublicBookingResult(
        ok=True,
        reference=f"BR-{appt.id:06d}",
        status=appt.status,
        doctor_name=doctor_name,
        scheduled_at=appt.scheduled_at,
    )
