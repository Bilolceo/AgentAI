"""Doctor + Appointment services (M2). Pure DB logic; no auth (gated at the API)."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import clinic_now
from app.models.appointment import (
    APPOINTMENT_SOURCES,
    APPOINTMENT_STATUSES,
    Appointment,
)
from app.models.doctor import Doctor


def short_name(name: Optional[str]) -> Optional[str]:
    """Shorten a patient name for manager lists: 'Aliyev Akmal' -> 'Aliyev A.'."""
    s = (name or "").strip()
    if not s:
        return None
    parts = s.split()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[1][0]}."


def _day_bounds(d: datetime) -> tuple[datetime, datetime]:
    start = d.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


class DoctorService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list(self, *, active_only: bool = False) -> list[Doctor]:
        stmt = select(Doctor)
        if active_only:
            stmt = stmt.where(Doctor.is_active.is_(True))
        stmt = stmt.order_by(Doctor.full_name.asc())
        return list((await self._s.execute(stmt)).scalars().all())

    async def get(self, doctor_id: int) -> Optional[Doctor]:
        return await self._s.get(Doctor, doctor_id)

    async def create(self, **fields) -> Doctor:
        doctor = Doctor(**fields)
        self._s.add(doctor)
        await self._s.flush()
        return doctor

    async def update(self, doctor_id: int, **fields) -> Optional[Doctor]:
        doctor = await self._s.get(Doctor, doctor_id)
        if doctor is None:
            return None
        for k, v in fields.items():
            if v is not None:
                setattr(doctor, k, v)
        await self._s.flush()
        return doctor


class AppointmentService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    def _validate(self, status: str, source: str) -> None:
        if status not in APPOINTMENT_STATUSES:
            raise ValueError(f"invalid status: {status}")
        if source not in APPOINTMENT_SOURCES:
            raise ValueError(f"invalid source: {source}")

    async def create(self, **fields) -> Appointment:
        self._validate(fields.get("status", "pending"), fields.get("source", "manual"))
        appt = Appointment(**fields)
        self._s.add(appt)
        await self._s.flush()
        return appt

    async def delete(self, appt_id: int) -> bool:
        """Hard-delete an appointment (e.g. an erroneous or test entry)."""
        appt = await self._s.get(Appointment, appt_id)
        if appt is None:
            return False
        await self._s.delete(appt)
        await self._s.flush()
        return True

    async def set_status(self, appt_id: int, status: str) -> Optional[Appointment]:
        if status not in APPOINTMENT_STATUSES:
            raise ValueError(f"invalid status: {status}")
        appt = await self._s.get(Appointment, appt_id)
        if appt is None:
            return None
        appt.status = status
        await self._s.flush()
        return appt

    async def list_range(self, start: datetime, end: datetime) -> list[Appointment]:
        """Appointments with scheduled_at in [start, end)."""
        stmt = (
            select(Appointment)
            .where(Appointment.scheduled_at >= start, Appointment.scheduled_at < end)
            .order_by(Appointment.scheduled_at.asc(), Appointment.id.asc())
        )
        return list((await self._s.execute(stmt)).scalars().all())

    async def list_day(self, day: datetime) -> list[Appointment]:
        start, end = _day_bounds(day)
        return await self.list_range(start, end)

    async def list_leads(self) -> list[Appointment]:
        """Web contact-form leads: no slot yet (scheduled_at NULL), status=new."""
        stmt = (
            select(Appointment)
            .where(
                Appointment.scheduled_at.is_(None),
                Appointment.source == "web",
                Appointment.status == "new",
            )
            .order_by(Appointment.created_at.desc())
        )
        return list((await self._s.execute(stmt)).scalars().all())

    async def doctor_workload(self, start: datetime, end: datetime) -> dict[int, int]:
        """Map doctor_id -> appointment count in [start, end)."""
        stmt = (
            select(Appointment.doctor_id, func.count())
            .where(
                Appointment.scheduled_at >= start,
                Appointment.scheduled_at < end,
                Appointment.doctor_id.is_not(None),
            )
            .group_by(Appointment.doctor_id)
        )
        rows = (await self._s.execute(stmt)).all()
        return {int(doc_id): int(n) for doc_id, n in rows}

    async def report(self, start: datetime, end: datetime) -> dict:
        """Aggregated counts for a date range (manager reports)."""
        appts = await self.list_range(start, end)
        by_status: dict[str, int] = {}
        ai_created = operator_required = cancelled = no_show = 0
        for a in appts:
            by_status[a.status] = by_status.get(a.status, 0) + 1
            if a.source == "ai_call":
                ai_created += 1
            if a.operator_required:
                operator_required += 1
            if a.status == "cancelled":
                cancelled += 1
            if a.status == "no_show":
                no_show += 1
        return {
            "total": len(appts),
            "by_status": by_status,
            "ai_created": ai_created,
            "operator_required": operator_required,
            "cancelled": cancelled,
            "no_show": no_show,
        }


def range_for(kind: str, now: Optional[datetime] = None) -> tuple[datetime, datetime]:
    """Date range for 'today' | 'week' | 'month' (clinic-local day boundaries)."""
    now = now or clinic_now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if kind == "week":
        return start, start + timedelta(days=7)
    if kind == "month":
        return start, start + timedelta(days=30)
    return start, start + timedelta(days=1)  # today (default)
