"""Admin API himoyasi — oddiy API key tekshiruvi.

TODO: TZ talab qilsa, JWT / role-based access qo'shish.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.config import settings


async def require_api_key(x_api_key: str = Header(default="")) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key",
        )
