"""TOTP (RFC 6238) + recovery codes — stdlib only, no external dependency."""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time

_STEP = 30
_DIGITS = 6


def generate_secret() -> str:
    """Base32 TOTP secret (no padding) for authenticator apps."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _hotp(secret_b32: str, counter: int) -> str:
    padding = "=" * (-len(secret_b32) % 8)
    key = base64.b32decode(secret_b32 + padding, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10**_DIGITS)).zfill(_DIGITS)


def totp_now(secret_b32: str, at: float | None = None) -> str:
    counter = int((at if at is not None else time.time()) // _STEP)
    return _hotp(secret_b32, counter)


def verify_totp(secret_b32: str, code: str, *, window: int = 1, at: float | None = None) -> bool:
    code = (code or "").strip()
    if not code:
        return False
    now = at if at is not None else time.time()
    base = int(now // _STEP)
    for drift in range(-window, window + 1):
        if hmac.compare_digest(_hotp(secret_b32, base + drift), code):
            return True
    return False


def otpauth_uri(secret_b32: str, email: str, issuer: str = "AI Call-Center") -> str:
    label = f"{issuer}:{email}"
    return (
        f"otpauth://totp/{label}?secret={secret_b32}&issuer={issuer}"
        f"&algorithm=SHA1&digits={_DIGITS}&period={_STEP}"
    )


def generate_recovery_codes(count: int = 10) -> list[str]:
    """Human-friendly single-use codes, e.g. 'a1b2c3d4-e5f6g7h8'."""
    return [f"{secrets.token_hex(4)}-{secrets.token_hex(4)}" for _ in range(count)]
