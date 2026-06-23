"""Public self-service booking logic (slot generation, availability, validation).

Customer-facing: no auth. Kept separate from the manager service so the public
surface stays small and auditable. All times use UTC to match the rest of the
app (the admin/rahbar calendar renders the stored HH:MM directly).
"""
from __future__ import annotations

import re
from datetime import datetime, time, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.doctor import Doctor

# Default clinic working window when a doctor has no explicit working_hours.
DEFAULT_OPEN = time(9, 0)
DEFAULT_CLOSE = time(18, 0)
SLOT_MINUTES = 30
LUNCH_START = time(13, 0)
LUNCH_END = time(14, 0)
# Default working week: Mon..Sat (clinic closed Sunday) when not set on the doctor.
DEFAULT_WORKING_DAYS = ("mon", "tue", "wed", "thu", "fri", "sat")
_DOW = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

# How far ahead the public can book, and how many active requests one phone may
# hold at once (basic anti-abuse; full rate limiting is at the API layer).
MAX_DAYS_AHEAD = 30
MAX_ACTIVE_PER_PHONE = 3

_PHONE_RE = re.compile(r"^\+998\d{9}$")
_NAME_RE = re.compile(r"^[\w\s.'-]{2,80}$", re.UNICODE)


class BookingError(ValueError):
    """A customer-facing booking validation failure (message is safe to show)."""


def normalize_phone(raw: str) -> str:
    """Normalize an Uzbek phone to +998XXXXXXXXX or raise BookingError."""
    s = re.sub(r"[\s()-]", "", (raw or "").strip())
    if s.startswith("998") and len(s) == 12:
        s = "+" + s
    elif s.startswith("8") and len(s) == 10:  # local 8XX... -> +998
        s = "+99" + s
    if not _PHONE_RE.match(s):
        raise BookingError("invalid_phone")
    return s


def validate_name(raw: str) -> str:
    s = (raw or "").strip()
    if not _NAME_RE.match(s):
        raise BookingError("invalid_name")
    return s


def _parse_hhmm(s: Optional[str], default: time) -> time:
    if not s:
        return default
    try:
        h, m = s.strip().split(":")
        return time(int(h), int(m))
    except (ValueError, AttributeError):
        return default


def doctor_hours(doctor: Doctor) -> tuple[time, time]:
    open_s = close_s = None
    if doctor.working_hours and "-" in doctor.working_hours:
        open_s, close_s = doctor.working_hours.split("-", 1)
    return _parse_hhmm(open_s, DEFAULT_OPEN), _parse_hhmm(close_s, DEFAULT_CLOSE)


def doctor_working_days(doctor: Doctor) -> tuple[str, ...]:
    if not doctor.working_days:
        return DEFAULT_WORKING_DAYS
    days = tuple(d.strip().lower() for d in doctor.working_days.split(",") if d.strip())
    return days or DEFAULT_WORKING_DAYS


def _as_utc(dt: datetime) -> datetime:
    """Normalize to tz-aware UTC (SQLite returns naive; Postgres returns aware)."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def parse_date(raw: str) -> datetime:
    """Parse 'YYYY-MM-DD' into a UTC midnight datetime or raise BookingError."""
    try:
        d = datetime.strptime((raw or "").strip(), "%Y-%m-%d")
    except ValueError as exc:
        raise BookingError("invalid_date") from exc
    return d.replace(tzinfo=timezone.utc)


def _candidate_times(open_t: time, close_t: time) -> list[time]:
    out: list[time] = []
    cur = datetime(2000, 1, 1, open_t.hour, open_t.minute)
    end = datetime(2000, 1, 1, close_t.hour, close_t.minute)
    step = timedelta(minutes=SLOT_MINUTES)
    while cur < end:
        t = cur.time()
        if not (LUNCH_START <= t < LUNCH_END):  # skip lunch break
            out.append(t)
        cur += step
    return out


class PublicBookingService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def services(self) -> list[dict]:
        """Distinct active-doctor specialties as bookable directions."""
        stmt = (
            select(Doctor.specialty, func.count())
            .where(Doctor.is_active.is_(True), Doctor.specialty.is_not(None))
            .group_by(Doctor.specialty)
            .order_by(Doctor.specialty.asc())
        )
        rows = (await self._s.execute(stmt)).all()
        return [{"specialty": s, "doctor_count": int(n)} for s, n in rows if s]

    async def doctors(self, specialty: Optional[str] = None) -> list[Doctor]:
        stmt = select(Doctor).where(Doctor.is_active.is_(True))
        if specialty:
            stmt = stmt.where(Doctor.specialty == specialty)
        stmt = stmt.order_by(Doctor.full_name.asc())
        return list((await self._s.execute(stmt)).scalars().all())

    async def _taken(self, doctor_id: int, day: datetime) -> set[datetime]:
        end = day + timedelta(days=1)
        stmt = select(Appointment.scheduled_at).where(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_at >= day,
            Appointment.scheduled_at < end,
            Appointment.status != "cancelled",
        )
        rows = (await self._s.execute(stmt)).scalars().all()
        return {_as_utc(r) for r in rows if r is not None}

    async def available_slots(self, doctor: Doctor, day: datetime) -> list[str]:
        """Free 'HH:MM' slots for a doctor on a given UTC day.

        Empty when the day is outside the booking window, in the past, or a
        non-working day for the doctor.
        """
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        horizon = today + timedelta(days=MAX_DAYS_AHEAD)
        if day < today or day > horizon:
            return []
        if _DOW[day.weekday()] not in doctor_working_days(doctor):
            return []

        open_t, close_t = doctor_hours(doctor)
        taken = await self._taken(doctor.id, day)
        slots: list[str] = []
        for t in _candidate_times(open_t, close_t):
            when = day.replace(hour=t.hour, minute=t.minute)
            if when <= now:  # no same-day past slots
                continue
            if when in taken:
                continue
            slots.append(f"{t.hour:02d}:{t.minute:02d}")
        return slots

    async def _active_count(self, phone: str) -> int:
        stmt = select(func.count()).where(
            Appointment.patient_phone == phone,
            Appointment.status.in_(("new", "pending", "confirmed")),
        )
        return int((await self._s.execute(stmt)).scalar_one())

    async def _slot_free(self, doctor_id: int, when: datetime) -> bool:
        stmt = select(func.count()).where(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_at == when,
            Appointment.status != "cancelled",
        )
        return int((await self._s.execute(stmt)).scalar_one()) == 0

    async def book(
        self,
        *,
        doctor_id: int,
        date: str,
        time_hhmm: str,
        patient_name: str,
        patient_phone: str,
        service: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Appointment:
        """Create a pending web appointment after full re-validation."""
        name = validate_name(patient_name)
        phone = normalize_phone(patient_phone)

        doctor = await self._s.get(Doctor, doctor_id)
        if doctor is None or not doctor.is_active:
            raise BookingError("doctor_unavailable")

        day = parse_date(date)
        slots = await self.available_slots(doctor, day)
        if time_hhmm not in slots:
            raise BookingError("slot_taken")

        if await self._active_count(phone) >= MAX_ACTIVE_PER_PHONE:
            raise BookingError("too_many_active")

        hh, mm = (int(x) for x in time_hhmm.split(":"))
        when = day.replace(hour=hh, minute=mm)
        # Final race-check inside the transaction before insert.
        if not await self._slot_free(doctor_id, when):
            raise BookingError("slot_taken")

        appt = Appointment(
            doctor_id=doctor_id,
            patient_name=name,
            patient_phone=phone,
            service=(service or doctor.specialty or "Konsultatsiya").strip(),
            scheduled_at=when,
            duration_minutes=SLOT_MINUTES,
            status="pending",
            source="web",
            operator_required=False,
            notes=(notes or "").strip() or None,
        )
        self._s.add(appt)
        await self._s.flush()
        return appt
