"""Password hashing (PBKDF2-HMAC-SHA256, stdlib — no plaintext stored)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os

_ITERATIONS = 120_000
_ALGO = "pbkdf2_sha256"

MIN_PASSWORD_LENGTH = 10


class PasswordPolicyError(ValueError):
    """Raised when a password fails the strength policy (message is safe to show)."""


def validate_password(password: str) -> None:
    """Enforce length + letter + digit. Never echoes the password itself."""
    if password is None or len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
        )
    if not any(c.isalpha() for c in password):
        raise PasswordPolicyError("Password must include at least one letter")
    if not any(c.isdigit() for c in password):
        raise PasswordPolicyError("Password must include at least one digit")


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ALGO}${_ITERATIONS}${_b64(salt)}${_b64(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_b64, hash_b64 = stored.split("$")
        if algo != _ALGO:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(dk, expected)
    except (ValueError, TypeError):
        return False
