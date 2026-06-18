"""Bookings — CRUD (admin)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import require_api_key
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingOut
from app.services.booking.service import BookingService

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("", response_model=list[BookingOut])
async def list_bookings(
    session: AsyncSession = Depends(get_session), limit: int = 50
) -> list[Booking]:
    rows = await session.execute(select(Booking).order_by(Booking.created_at.desc()).limit(limit))
    return list(rows.scalars().all())


@router.post("", response_model=BookingOut, status_code=201)
async def create(
    payload: BookingCreate, session: AsyncSession = Depends(get_session)
) -> Booking:
    booking = await BookingService(session).create(
        service=payload.service,
        scheduled_at=payload.scheduled_at,
        customer_id=payload.customer_id,
        call_id=payload.call_id,
        notes=payload.notes,
    )
    await session.commit()
    return booking
