"""FastAPI auth dependencies: current user, role guards, and 2FA ticket."""
from __future__ import annotations

from collections.abc import Callable
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.admin_user import AdminUser
from app.services.auth.service import AuthService
from app.services.auth.tokens import (
    ACCESS_SCOPE,
    TWO_FACTOR_SCOPE,
    TokenError,
    decode_access_token,
)


def _bearer(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    return authorization[7:].strip()


async def _user_from_token(token: str, *, scope: str, session: AsyncSession) -> AdminUser:
    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    if payload.get("scope") != scope:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token scope")
    user = await AuthService(session).get_by_id(int(payload.get("sub", 0)))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or unknown user"
        )
    # Access tokens carry a version that must match the user's current version.
    if scope == ACCESS_SCOPE and payload.get("ver") != user.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    return user


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> AdminUser:
    """Authenticated user. Allowed even when a password change is pending
    (so /auth/me and /auth/change-password remain reachable)."""
    return await _user_from_token(_bearer(authorization), scope=ACCESS_SCOPE, session=session)


async def get_current_user_active(user: AdminUser = Depends(get_current_user)) -> AdminUser:
    """Authenticated AND not blocked by a pending forced password change."""
    if user.force_password_change:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="password_change_required")
    return user


async def get_two_factor_user(
    authorization: Optional[str] = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> AdminUser:
    """Resolve the user from a 2FA ticket only (cannot reach admin endpoints)."""
    return await _user_from_token(_bearer(authorization), scope=TWO_FACTOR_SCOPE, session=session)


def require_roles(*roles: str) -> Callable:
    async def _guard(user: AdminUser = Depends(get_current_user_active)) -> AdminUser:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role"
            )
        return user

    return _guard
