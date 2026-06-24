"""NotificationService — SMS / Telegram dispatch.

Default channel is "mock": it only logs (no real send, no credentials needed).
Real channels (Eskiz.uz for Uzbekistan, Twilio) are selected via settings and
share the same interface. `dispatch()` never raises — it returns the outcome so
callers can record it without breaking the booking/confirmation flow.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.notifications.sms import send_eskiz, send_sms

log = get_logger("notifications")


@dataclass
class DispatchResult:
    status: str  # mock | sent | failed
    provider_ref: Optional[str] = None
    error: Optional[str] = None


class NotificationService:
    def __init__(self, *, channel: Optional[str] = None) -> None:
        self._channel = channel or settings.notifications_channel

    @property
    def channel(self) -> str:
        return self._channel

    async def send(self, *, to: str, body: str) -> None:
        """Best-effort fire-and-forget send (legacy callers)."""
        self.dispatch(to=to, body=body)

    def dispatch(self, *, to: str, body: str) -> DispatchResult:
        """Send via the configured channel. Never raises."""
        if self._channel == "mock" or not to:
            log.info("notification_mock", channel=self._channel, to=to, body=body)
            return DispatchResult(status="mock")
        try:
            if self._channel == "eskiz":
                ref = send_eskiz(to=to, body=body)
            elif self._channel == "twilio":
                ref = send_sms(to=to, body=body)
            else:
                log.warning("notification_unknown_channel", channel=self._channel)
                return DispatchResult(status="mock")
            return DispatchResult(status="sent", provider_ref=ref or None)
        except Exception as exc:  # noqa: BLE001 — best-effort; record and move on
            log.error("notification_failed", channel=self._channel, to=to, error=str(exc))
            return DispatchResult(status="failed", error=str(exc)[:500])

    async def schedule_reminder(self, *, to: str, body: str, when_iso: str) -> None:
        # TODO: enqueue a Celery reminder task; for now just record intent.
        log.info("reminder_scheduled", to=to, when=when_iso, body=body)
