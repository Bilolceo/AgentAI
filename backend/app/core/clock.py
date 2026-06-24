"""Clinic time helpers.

Appointment `scheduled_at` values are stored as the clinic's wall-clock time
tagged with UTC (the display layer renders them verbatim, e.g. "09:00"). To
compare "now" against those stored values correctly, we take the clinic-local
wall-clock and stamp it UTC the same way, instead of using true UTC (which would
be off by the clinic offset, e.g. 5 hours for Uzbekistan).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import settings


def clinic_now() -> datetime:
    """Current clinic wall-clock, stamped UTC to match stored appointment times."""
    offset = timedelta(hours=settings.clinic_utc_offset_hours)
    return (datetime.now(timezone.utc) + offset).replace(tzinfo=timezone.utc)
