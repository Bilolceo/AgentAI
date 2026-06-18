"""Minimal HS256 JWT (stdlib). Secret + expiry come from settings/env.

Self-contained so the pilot needs no extra dependency; swap for PyJWT later if
desired without changing call sites.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from app.core.config import settings


class TokenError(Exception):
    """Raised on a missing/invalid/expired token."""


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: bytes) -> bytes:
    return hmac.new(settings.jwt_secret.encode("utf-8"), message, hashlib.sha256).digest()


ACCESS_SCOPE = "access"
TWO_FACTOR_SCOPE = "2fa_ticket"


def _encode(payload: dict) -> str:
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    segments = [
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode("ascii")
    segments.append(_b64url_encode(_sign(signing_input)))
    return ".".join(segments)


def create_access_token(
    *, subject: str, role: str, token_version: int, expires_minutes: int | None = None
) -> str:
    exp_minutes = (
        expires_minutes if expires_minutes is not None else settings.access_token_expire_minutes
    )
    return _encode(
        {
            "sub": subject,
            "role": role,
            "ver": token_version,
            "scope": ACCESS_SCOPE,
            "exp": int(time.time()) + exp_minutes * 60,
        }
    )


def create_two_factor_ticket(*, subject: str) -> str:
    """Short-lived token that ONLY completes 2FA login (no admin access)."""
    return _encode(
        {
            "sub": subject,
            "scope": TWO_FACTOR_SCOPE,
            "exp": int(time.time()) + settings.two_factor_ticket_expire_minutes * 60,
        }
    )


def decode_access_token(token: str) -> dict:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = _sign(signing_input)
        if not hmac.compare_digest(expected_sig, _b64url_decode(sig_b64)):
            raise TokenError("bad signature")
        payload = json.loads(_b64url_decode(payload_b64))
    except TokenError:
        raise
    except Exception as exc:  # malformed base64/json/structure
        raise TokenError("malformed token") from exc

    if int(payload.get("exp", 0)) < int(time.time()):
        raise TokenError("token expired")
    return payload
