from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    email: str
    password: str


class BootstrapRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class UserOut(BaseModel):
    """Public user shape — never includes password_hash."""

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


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginResult(BaseModel):
    """Either a full token (2FA off) or a 2FA challenge (2FA on)."""

    two_factor_required: bool = False
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    user: Optional[UserOut] = None
    two_factor_ticket: Optional[str] = None


class TwoFactorCodeRequest(BaseModel):
    code: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class EnrollResponse(BaseModel):
    secret: str
    otpauth_uri: str


class RecoveryCodesResponse(BaseModel):
    recovery_codes: list[str]
