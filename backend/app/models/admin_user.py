from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AdminUser(Base):
    """Dashboard user with a role (TZ §8.5). 2FA fields are reserved for A6.2."""

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16))  # super_admin | admin | operator
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Bumped to invalidate all previously issued access tokens for this user.
    token_version: Mapped[int] = mapped_column(default=1)
    force_password_change: Mapped[bool] = mapped_column(Boolean, default=False)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String(64))  # base32 TOTP secret
    # Hashed single-use recovery codes (never plaintext, never serialized).
    two_factor_recovery_codes: Mapped[Optional[list]] = mapped_column(JSON)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
