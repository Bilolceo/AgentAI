"""MockTelephonyProvider — deterministic local provider for tests/dev.

Accepts a JSON webhook payload, optionally authenticates a shared secret via the
`X-Telephony-Secret` header, and normalizes the payload into an InboundCallEvent.
No external calls.
"""
from __future__ import annotations

import json
from typing import Optional

from app.services.telephony.provider import (
    InboundCallEvent,
    TelephonyParseError,
    TelephonyProvider,
    ValidationResult,
    VoiceResponse,
)

_SECRET_HEADER = "x-telephony-secret"
# Keys copied verbatim into raw_metadata (safe, non-sensitive only).
_SAFE_KEYS = ("provider_call_id", "from_number", "to_number", "language", "event")


class MockTelephonyProvider(TelephonyProvider):
    name = "mock"

    def __init__(self, webhook_secret: str = "") -> None:
        self._secret = webhook_secret

    def validate_inbound_request(self, *, headers: dict, body: bytes) -> ValidationResult:
        # Only enforce the secret when one is configured.
        if not self._secret:
            return ValidationResult(ok=True)
        provided = headers.get(_SECRET_HEADER)
        if provided and provided == self._secret:
            return ValidationResult(ok=True)
        # Do NOT echo the provided/expected secret in the reason.
        return ValidationResult(ok=False, reason="invalid_webhook_secret")

    def parse_inbound_call(self, *, headers: dict, body: bytes) -> InboundCallEvent:
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except (ValueError, UnicodeDecodeError) as exc:
            raise TelephonyParseError("malformed JSON payload") from exc
        if not isinstance(data, dict):
            raise TelephonyParseError("payload must be a JSON object")

        text_override = _str_or_none(data.get("text_override"))
        audio_base64 = _str_or_none(data.get("audio_base64"))
        if not text_override and not audio_base64:
            raise TelephonyParseError("provide text_override or audio_base64")

        raw_metadata = {k: data[k] for k in _SAFE_KEYS if k in data and data[k] is not None}
        return InboundCallEvent(
            provider=self.name,
            provider_call_id=_str_or_none(data.get("provider_call_id")),
            from_number=_str_or_none(data.get("from_number")),
            to_number=_str_or_none(data.get("to_number")),
            language=_str_or_none(data.get("language")),
            text_override=text_override,
            audio_base64=audio_base64,
            content_type=_str_or_none(data.get("content_type")),
            call_session_id=_int_or_none(data.get("call_session_id")),
            raw_metadata=raw_metadata,
        )

    def build_voice_response(self, outcome) -> VoiceResponse:
        audio = None
        if outcome.audio is not None:
            audio = {
                "voice": outcome.audio.voice,
                "language": outcome.audio.language,
                "content_type": outcome.audio.content_type,
                "duration_ms": outcome.audio.duration_ms,
                "audio_bytes_len": len(outcome.audio.audio_bytes or b""),
                "provider": outcome.audio.provider_metadata.get("provider"),
            }
        return VoiceResponse(
            provider=self.name,
            content_type="application/json",
            payload={
                "provider": self.name,
                "call_session_id": outcome.call_id,
                "ai_text": outcome.ai_text,
                "action": outcome.action,
                "transferred": outcome.transferred,
                "language": outcome.language,
                "audio": audio,  # metadata only; never raw bytes
            },
        )


def _str_or_none(v) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _int_or_none(v) -> Optional[int]:
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
