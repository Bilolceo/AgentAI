"""Twilio SMS channel (used by NotificationService once enabled).

Twilio is imported lazily so the MVP/mock path never requires the dependency.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("notifications.sms")


def send_sms(*, to: str, body: str) -> str:
    from twilio.rest import Client  # lazy import — not needed for the MVP mock path

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    msg = client.messages.create(to=to, from_=settings.twilio_phone_number, body=body)
    log.info("sms_sent", to=to, sid=msg.sid)
    return msg.sid
