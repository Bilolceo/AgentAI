"""BookingService — appointment creation.

MVP persists a basic Booking row. Availability checks, working-hours rules and
Google Calendar / CRM sync are added per the TZ later.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.booking import Booking

log = get_logger("booking")


class BookingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        service: str,
        scheduled_at: datetime | str | None = None,
        customer_id: int | None = None,
        call_id: int | None = None,
        notes: str | None = None,
    ) -> Booking:
        parsed_at: datetime | None
        if isinstance(scheduled_at, str):
            try:
                parsed_at = datetime.fromisoformat(scheduled_at)
            except ValueError:
                log.warning("bad_scheduled_at", value=scheduled_at)
                parsed_at = None
        else:
            parsed_at = scheduled_at

        booking = Booking(
            service=service,
            scheduled_at=parsed_at,
            customer_id=customer_id,
            call_id=call_id,
            notes=notes,
            status="pending",  # TODO: "confirmed" after availability check
        )
        self._session.add(booking)
        await self._session.flush()
        log.info("booking_created", id=booking.id, service=service)
        return booking
