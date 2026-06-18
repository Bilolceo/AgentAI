"""BookingService tests (in-memory SQLite)."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.services.booking.service import BookingService


@pytest.mark.asyncio
async def test_create_booking_persists(db_session: AsyncSession) -> None:
    booking = await BookingService(db_session).create(
        service="Konsultatsiya", scheduled_at="2026-07-01T10:00:00", notes="uz"
    )
    await db_session.commit()

    stored = await db_session.scalar(select(Booking).where(Booking.id == booking.id))
    assert stored is not None
    assert stored.service == "Konsultatsiya"
    assert stored.status == "pending"
    assert stored.scheduled_at is not None


@pytest.mark.asyncio
async def test_create_booking_bad_date_is_tolerated(db_session: AsyncSession) -> None:
    booking = await BookingService(db_session).create(
        service="Tahlil", scheduled_at="not-a-date"
    )
    await db_session.commit()
    assert booking.scheduled_at is None
    assert booking.service == "Tahlil"
