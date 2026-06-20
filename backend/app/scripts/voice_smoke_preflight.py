"""Offline preflight checker for the live-call smoke test (A32).

Validates that the environment is configured for a controlled real smoke call
(Twilio + Deepgram STT + Deepgram TTS) BEFORE anyone places a call. It is OFFLINE:
it reads config only and NEVER contacts Twilio, Deepgram, Railway, or any network.
It prints only safe booleans and config NAMES - never a secret VALUE.

It reuses the same VoiceProviderReadinessService used by the admin readiness
endpoint, then layers a few smoke-execution-specific checks (Twilio auth token must
be present so the stream token can be signed; the smoke hard caps must be positive
and bounded).

Run:
    cd backend && python -m app.scripts.voice_smoke_preflight

Exit code:
    0  -> ready (possibly with non-blocking warnings)
    1  -> blocking errors (do NOT run the live call)
"""
from __future__ import annotations

import sys

from app.services.voice.readiness import VoiceProviderReadinessService

# Upper sanity bounds for the smoke-call hard caps (cost/safety guard). A value
# above these is a blocking error so a real call cannot run unbounded.
_MAX_DURATION_CEILING_SECONDS = 600  # 10 minutes
_MAX_TURNS_CEILING = 50


def build_preflight_settings():
    """A fresh Settings() instance reads the current environment (.env + os.environ)
    without mutating the cached global settings."""
    from app.core.config import Settings

    return Settings()


def run_preflight(settings=None) -> dict:
    """Return {ready, errors, warnings, summary}. Pure; no network, no secrets."""
    if settings is None:
        settings = build_preflight_settings()
    result = VoiceProviderReadinessService(settings).check()
    errors = list(result["errors"])
    warnings = list(result["warnings"])

    # Smoke-execution-specific checks beyond the base readiness service.
    if settings.live_call_smoke_mode:
        # The media-stream stream_token is signed with the Twilio auth token.
        if settings.telephony_provider == "twilio" and not settings.twilio_auth_token:
            errors.append(
                "TWILIO_AUTH_TOKEN missing - the media-stream stream_token cannot be signed"
            )
        if not settings.public_base_url or settings.public_base_url.startswith("http://localhost"):
            warnings.append(
                "PUBLIC_BASE_URL is not a public https URL - Twilio cannot reach the stream"
            )
        dur = int(settings.live_call_max_duration_seconds)
        turns = int(settings.live_call_max_turns)
        if dur <= 0:
            errors.append("LIVE_CALL_MAX_DURATION_SECONDS must be > 0 in smoke mode")
        elif dur > _MAX_DURATION_CEILING_SECONDS:
            errors.append(
                f"LIVE_CALL_MAX_DURATION_SECONDS too high (> {_MAX_DURATION_CEILING_SECONDS}); "
                "keep smoke calls short"
            )
        if turns <= 0:
            errors.append("LIVE_CALL_MAX_TURNS must be > 0 in smoke mode")
        elif turns > _MAX_TURNS_CEILING:
            errors.append(
                f"LIVE_CALL_MAX_TURNS too high (> {_MAX_TURNS_CEILING}); keep smoke calls bounded"
            )

    return {
        "ready": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": result["summary"],
    }


def format_preflight(result: dict) -> str:
    """Render a SAFE plain-text report (booleans + config names only, no values)."""
    lines: list[str] = []
    lines.append("Live-call smoke preflight (offline; no network, no secrets)")
    lines.append(f"ready: {str(result['ready']).lower()}")
    lines.append("")
    lines.append(f"errors ({len(result['errors'])}):")
    for e in result["errors"]:
        lines.append(f"  - {e}")
    if not result["errors"]:
        lines.append("  (none)")
    lines.append("")
    lines.append(f"warnings ({len(result['warnings'])}):")
    for w in result["warnings"]:
        lines.append(f"  - {w}")
    if not result["warnings"]:
        lines.append("  (none)")
    lines.append("")
    lines.append("config summary (safe; *_present are booleans, no secret values):")
    for k, v in result["summary"].items():
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def main() -> int:
    result = run_preflight()
    print(format_preflight(result))
    return 0 if result["ready"] else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
