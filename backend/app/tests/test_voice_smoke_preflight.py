"""Offline preflight checker for the live-call smoke test (A32).

Pure config validation - no network, no real secrets. Each test builds a Settings
instance from explicit kwargs (never the real environment) so it is deterministic.
"""
from __future__ import annotations

from app.core.config import Settings
from app.scripts.voice_smoke_preflight import format_preflight, run_preflight

_SECRET = "DG-REAL-SECRET-VALUE-123"
_TOKEN = "SMOKE-REAL-TOKEN-VALUE-456"


def _settings(**over) -> Settings:
    """A fully real-pipeline smoke config; override individual fields per test."""
    base = dict(
        telephony_provider="twilio",
        twilio_auth_token="tw-auth",
        public_base_url="https://clinic.example",
        twilio_use_media_streams=True,
        streaming_stt_enabled=True,
        streaming_stt_ai_turns_enabled=True,
        streaming_tts_enabled=True,
        streaming_stt_provider="deepgram",
        streaming_tts_provider="deepgram",
        deepgram_api_key=_SECRET,
        deepgram_encoding="mulaw",
        deepgram_sample_rate=8000,
        deepgram_tts_encoding="mulaw",
        deepgram_tts_sample_rate=8000,
        deepgram_tts_container="none",
        barge_in_enabled=True,
        streaming_metrics_enabled=True,
        live_call_smoke_mode=True,
        live_call_require_smoke_token=True,
        live_call_smoke_token=_TOKEN,
        live_call_allowed_caller_numbers="+998901112233",
        live_call_redact_transcripts=True,
        live_call_max_duration_seconds=180,
        live_call_max_turns=10,
    )
    base.update(over)
    return Settings(**base)


def test_valid_setup_is_ready() -> None:
    r = run_preflight(_settings())
    assert r["ready"] is True and r["errors"] == []


def test_missing_deepgram_key_is_blocking_no_leak() -> None:
    r = run_preflight(_settings(deepgram_api_key=""))
    assert r["ready"] is False
    assert any("DEEPGRAM_API_KEY" in e for e in r["errors"])
    assert _SECRET not in format_preflight(r)  # the (now-empty) key is not echoed
    assert r["summary"]["deepgram_api_key_present"] is False


def test_tts_encoding_wrong_is_blocking() -> None:
    r = run_preflight(_settings(deepgram_tts_encoding="linear16"))
    assert r["ready"] is False
    assert any("TTS" in e and "Twilio-compatible" in e for e in r["errors"])
    assert r["summary"]["tts_twilio_compatible"] is False


def test_tts_container_wrong_is_blocking() -> None:
    r = run_preflight(_settings(deepgram_tts_container="wav"))
    assert r["ready"] is False
    assert r["summary"]["tts_twilio_compatible"] is False


def test_tts_sample_rate_wrong_is_blocking() -> None:
    r = run_preflight(_settings(deepgram_tts_sample_rate=16000))
    assert r["ready"] is False
    assert r["summary"]["tts_twilio_compatible"] is False


def test_smoke_token_missing_while_required_is_blocking() -> None:
    r = run_preflight(_settings(live_call_smoke_token=""))
    assert r["ready"] is False
    assert any("LIVE_CALL_SMOKE_TOKEN" in e for e in r["errors"])


def test_missing_twilio_auth_token_is_blocking() -> None:
    r = run_preflight(_settings(twilio_auth_token=""))
    assert r["ready"] is False
    assert any("TWILIO_AUTH_TOKEN" in e for e in r["errors"])


def test_unbounded_duration_is_blocking() -> None:
    assert run_preflight(_settings(live_call_max_duration_seconds=0))["ready"] is False
    assert run_preflight(_settings(live_call_max_duration_seconds=99999))["ready"] is False


def test_unbounded_turns_is_blocking() -> None:
    assert run_preflight(_settings(live_call_max_turns=0))["ready"] is False
    assert run_preflight(_settings(live_call_max_turns=9999))["ready"] is False


def test_localhost_public_url_is_warning_not_blocking() -> None:
    r = run_preflight(_settings(public_base_url="http://localhost:8000"))
    # Not blocking on its own (other fields valid), but warned.
    assert any("PUBLIC_BASE_URL" in w for w in r["warnings"])


def test_smoke_mode_off_skips_smoke_checks() -> None:
    # With smoke mode off and mock providers, preflight is ready (warnings only).
    r = run_preflight(Settings(live_call_smoke_mode=False))
    assert r["ready"] is True


def test_output_never_contains_secret_values() -> None:
    text = format_preflight(run_preflight(_settings()))
    assert _SECRET not in text and _TOKEN not in text
    # presence booleans are shown instead of values
    assert "deepgram_api_key_present: True" in text
    assert "smoke_token_present: True" in text


def test_format_is_plain_ascii_safe() -> None:
    text = format_preflight(run_preflight(_settings()))
    assert text.isascii()
    assert text.startswith("Live-call smoke preflight")
