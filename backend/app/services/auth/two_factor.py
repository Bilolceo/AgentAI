"""TwoFactorService — TOTP enrollment, confirmation, login verification.

Secrets and recovery codes are stored on the user; recovery codes are stored as
PBKDF2 hashes (never plaintext) and are single-use.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.services.auth.password import hash_password, verify_password
from app.services.auth.totp import (
    generate_recovery_codes,
    generate_secret,
    otpauth_uri,
    verify_totp,
)


class TwoFactorError(Exception):
    """Raised on an invalid 2FA state or code."""


class TwoFactorService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enroll(self, user: AdminUser) -> tuple[str, str]:
        """Generate a pending secret (not enabled until confirmed)."""
        if user.two_factor_enabled:
            raise TwoFactorError("2FA already enabled")
        secret = generate_secret()
        user.two_factor_secret = secret
        await self._session.flush()
        return secret, otpauth_uri(secret, user.email)

    async def confirm(self, user: AdminUser, code: str) -> list[str]:
        """Verify the first code, enable 2FA, and return one-time recovery codes."""
        if user.two_factor_enabled:
            raise TwoFactorError("2FA already enabled")
        if not user.two_factor_secret:
            raise TwoFactorError("No pending enrollment")
        if not verify_totp(user.two_factor_secret, code):
            raise TwoFactorError("Invalid code")
        codes = generate_recovery_codes()
        user.two_factor_recovery_codes = [hash_password(c) for c in codes]
        user.two_factor_enabled = True
        await self._session.flush()
        return codes

    async def verify_login(self, user: AdminUser, code: str) -> bool:
        """Accept a current TOTP code or consume a single-use recovery code."""
        if not user.two_factor_enabled or not user.two_factor_secret:
            return False
        if verify_totp(user.two_factor_secret, code):
            return True
        code = (code or "").strip()
        remaining = list(user.two_factor_recovery_codes or [])
        for h in remaining:
            if verify_password(code, h):
                remaining.remove(h)
                user.two_factor_recovery_codes = remaining
                await self._session.flush()
                return True
        return False

    async def disable(self, user: AdminUser, code: str) -> None:
        if not user.two_factor_enabled:
            raise TwoFactorError("2FA not enabled")
        if not await self.verify_login(user, code):
            raise TwoFactorError("Invalid code")
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_recovery_codes = None
        await self._session.flush()

    async def regenerate_recovery_codes(self, user: AdminUser, code: str) -> list[str]:
        if not user.two_factor_enabled or not user.two_factor_secret:
            raise TwoFactorError("2FA not enabled")
        if not verify_totp(user.two_factor_secret, code):
            raise TwoFactorError("Invalid code")
        codes = generate_recovery_codes()
        user.two_factor_recovery_codes = [hash_password(c) for c in codes]
        await self._session.flush()
        return codes
