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


def send_eskiz(*, to: str, body: str) -> str:
    """Send an SMS via Eskiz.uz (Uzbekistan). Returns the provider message id.

    httpx is imported lazily so the mock path never requires it. The auth token
    is fetched per call (low volume); cache it later if needed.
    """
    import httpx  # lazy import — only on the real Eskiz path

    base = settings.eskiz_base_url.rstrip("/")
    mobile = to.lstrip("+")  # Eskiz expects 998XXXXXXXXX
    with httpx.Client(timeout=15) as client:
        auth = client.post(
            f"{base}/auth/login",
            data={"email": settings.eskiz_email, "password": settings.eskiz_password},
        )
        auth.raise_for_status()
        token = auth.json()["data"]["token"]
        resp = client.post(
            f"{base}/message/sms/send",
            headers={"Authorization": f"Bearer {token}"},
            data={"mobile_phone": mobile, "message": body, "from": settings.eskiz_sender},
        )
        resp.raise_for_status()
        payload = resp.json()
        ref = str(payload.get("id") or payload.get("message_id") or "")
    log.info("eskiz_sms_sent", to=to, ref=ref)
    return ref
