"""TelephonyProvider interface + shared dataclasses/errors.

A provider turns a raw inbound webhook (headers + body) into a normalized
InboundCallEvent, and turns a pipeline VoiceOutcome into a provider response
payload. Real media streaming / barge-in are intentionally out of scope here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ValidationResult:
    """Outcome of webhook authentication (signature/secret check)."""

    ok: bool
    reason: Optional[str] = None  # safe, non-sensitive reason string


@dataclass
class InboundCallEvent:
    """Normalized inbound call, provider-agnostic."""

    provider: str
    provider_call_id: Optional[str] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    language: Optional[str] = None
    # One of these drives the pipeline (text is the deterministic local path).
    text_override: Optional[str] = None
    audio_base64: Optional[str] = None
    content_type: Optional[str] = None
    # Attach to an existing CallSession instead of starting a new one.
    call_session_id: Optional[int] = None
    # Twilio Voice fields (non-streaming Gather flow). All optional.
    account_sid: Optional[str] = None
    call_status: Optional[str] = None
    direction: Optional[str] = None
    speech_result: Optional[str] = None
    confidence: Optional[float] = None
    recording_url: Optional[str] = None
    # SAFE subset of the raw payload (never secrets/signatures) for audit/storage.
    raw_metadata: dict = field(default_factory=dict)


@dataclass
class VoiceResponse:
    """Provider-facing response built from a pipeline outcome."""

    provider: str
    content_type: str  # e.g. application/json (mock) or application/xml (TwiML)
    payload: dict


class TelephonyError(Exception):
    """Base telephony error."""


class TelephonySignatureError(TelephonyError):
    """Signature/secret validation failed (-> 401/403). No secret in the message."""


class TelephonyParseError(TelephonyError):
    """The provider could not parse the inbound payload (-> 400)."""


class TelephonyProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    def validate_inbound_request(
        self, *, headers: dict, body: bytes
    ) -> ValidationResult:
        """Authenticate the webhook (signature/secret). Never log the secret."""
        raise NotImplementedError

    @abstractmethod
    def parse_inbound_call(self, *, headers: dict, body: bytes) -> InboundCallEvent:
        """Parse the raw webhook into a normalized InboundCallEvent."""
        raise NotImplementedError

    @abstractmethod
    def build_voice_response(self, outcome) -> VoiceResponse:
        """Build the provider response payload from a VoiceOutcome."""
        raise NotImplementedError

    def parse_media_event(self, *, headers: dict, body: bytes):
        """Media streaming is out of scope for this spike."""
        raise NotImplementedError("Media streaming is not implemented in this spike")
