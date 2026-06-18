from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AdminUserOut(BaseModel):
    """Safe user shape — never includes password_hash / 2FA secret / recovery."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    two_factor_enabled: bool
    force_password_change: bool = False
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserCreate(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: str
    password: str
    is_active: bool = True
    force_password_change: bool = False


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None


class PasswordReset(BaseModel):
    new_password: str
