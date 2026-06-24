"""Send + record a patient-facing appointment SMS.

One entry point used by both the public booking flow and the manager status
change. Best-effort: a send failure is logged (NotificationLog.status="failed")
but never breaks the caller's transaction.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.appointment import Appointment
from app.models.notification_log import NotificationLog
from app.services.notifications.messages import appointment_sms_text
from app.services.notifications.service import NotificationService

log = get_logger("notifications.appointment")


async def notify_appointment(
    session: AsyncSession,
    appt: Appointment,
    kind: str,
    *,
    doctor_name: Optional[str] = None,
    locale: str = "uz",
) -> Optional[NotificationLog]:
    """Compose, dispatch and log an appointment SMS. Returns the log row (or None
    when there is no phone to send to)."""
    phone = (appt.patient_phone or "").strip()
    if not phone:
        return None

    body = appointment_sms_text(
        kind=kind,
        patient_name=appt.patient_name,
        scheduled_at=appt.scheduled_at,
        doctor_name=doctor_name,
        locale=locale,
    )
    svc = NotificationService()
    result = svc.dispatch(to=phone, body=body)

    entry = NotificationLog(
        appointment_id=appt.id,
        to_phone=phone,
        channel=svc.channel,
        kind=kind,
        body=body,
        status=result.status,
        provider_ref=result.provider_ref,
        error=result.error,
    )
    session.add(entry)
    await session.flush()
    return entry
