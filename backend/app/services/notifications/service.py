"""NotificationService — SMS / Telegram reminders.

MVP uses a mock channel that only logs. Real SMS (Twilio) / Telegram are wired in
later via the channel implementations; the service interface stays the same.
"""
from __future__ import annotations

from app.core.logging import get_logger

log = get_logger("notifications")


class NotificationService:
    def __init__(self, *, channel: str = "mock") -> None:
        self._channel = channel

    async def send(self, *, to: str, body: str) -> None:
        # TODO: dispatch via Twilio SMS / Telegram once enabled.
        log.info("notification_sent", channel=self._channel, to=to, body=body)

    async def schedule_reminder(self, *, to: str, body: str, when_iso: str) -> None:
        # TODO: enqueue a Celery reminder task; for now just record intent.
        log.info("reminder_scheduled", to=to, when=when_iso, body=body)
