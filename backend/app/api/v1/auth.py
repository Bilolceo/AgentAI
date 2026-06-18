"""Auth endpoints: login (+2FA, lockout), me, change-password, 2FA mgmt, bootstrap.

Logic lives in services; handlers orchestrate. Never logs raw passwords/codes/tokens.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.models.admin_user import AdminUser
from app.schemas.auth import (
    BootstrapRequest,
    ChangePasswordRequest,
    EnrollResponse,
    LoginRequest,
    LoginResult,
    RecoveryCodesResponse,
    TokenResponse,
    TwoFactorCodeRequest,
    UserOut,
)
from app.services.audit.log import AuditEvent, AuditLogService
from app.services.auth.attempts import AuthAttemptService
from app.services.auth.deps import get_current_user, get_current_user_active, get_two_factor_user
from app.services.auth.password import (
    PasswordPolicyError,
    hash_password,
    validate_password,
    verify_password,
)
from app.services.auth.service import AuthService
from app.services.auth.tokens import create_access_token, create_two_factor_ticket
from app.services.auth.two_factor import TwoFactorError, TwoFactorService

router = APIRouter()

_LOCKED = status.HTTP_423_LOCKED


def _access_token(user: AdminUser) -> str:
    return create_access_token(subject=str(user.id), role=user.role, token_version=user.token_version)


async def _record_failure(session: AsyncSession, audit: AuditLogService, email: str, **data) -> None:
    locked = AuthAttemptService.record_failure(email)
    await audit.record(AuditEvent.LOGIN_FAILED, actor=email, data={"email": email, **data})
    if locked:
        await audit.record(AuditEvent.AUTH_LOCKED, actor=email, data={"email": email})


@router.post("/login", response_model=LoginResult)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)) -> LoginResult:
    auth = AuthService(session)
    audit = AuditLogService(session)
    email = payload.email.lower()

    if AuthAttemptService.is_locked(email):
        raise HTTPException(status_code=_LOCKED, detail="Account temporarily locked. Try again later.")

    user = await auth.authenticate(payload.email, payload.password)
    if user is None:
        await _record_failure(session, audit, email)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials or inactive user"
        )

    AuthAttemptService.reset(email)
    if user.two_factor_enabled:
        ticket = create_two_factor_ticket(subject=str(user.id))
        await audit.record(AuditEvent.LOGIN_2FA_REQUIRED, actor=user.email, actor_user_id=user.id, data={"user_id": user.id})
        await session.commit()
        return LoginResult(two_factor_required=True, two_factor_ticket=ticket)

    await audit.record(AuditEvent.LOGIN_SUCCESS, actor=user.email, actor_user_id=user.id, data={"user_id": user.id})
    await session.commit()
    return LoginResult(access_token=_access_token(user), token_type="bearer", user=UserOut.model_validate(user))


@router.post("/login/2fa", response_model=TokenResponse)
async def login_2fa(
    payload: TwoFactorCodeRequest,
    user: AdminUser = Depends(get_two_factor_user),
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    audit = AuditLogService(session)
    if AuthAttemptService.is_locked(user.email):
        raise HTTPException(status_code=_LOCKED, detail="Account temporarily locked. Try again later.")

    if not await TwoFactorService(session).verify_login(user, payload.code):
        await _record_failure(session, audit, user.email, user_id=user.id, stage="2fa")
        await session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")

    AuthAttemptService.reset(user.email)
    user.last_login_at = datetime.now(timezone.utc)
    await audit.record(AuditEvent.LOGIN_SUCCESS, actor=user.email, actor_user_id=user.id, data={"user_id": user.id, "stage": "2fa"})
    await session.commit()
    return TokenResponse(access_token=_access_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(user: AdminUser = Depends(get_current_user)) -> AdminUser:
    return user


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    user: AdminUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")
    try:
        validate_password(payload.new_password)
    except PasswordPolicyError as exc:
        await AuditLogService(session).record(
            AuditEvent.WEAK_PASSWORD_REJECTED, actor=user.email, data={"user_id": user.id}
        )
        await session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user.password_hash = hash_password(payload.new_password)
    user.force_password_change = False
    user.token_version += 1  # invalidate the token used for this request
    await AuditLogService(session).record(
        AuditEvent.PASSWORD_CHANGE_SUCCESS, actor=user.email, actor_user_id=user.id, data={"user_id": user.id}
    )
    await session.commit()
    return {"status": "password_changed"}


# --- 2FA management (blocked while a password change is pending) ------------
@router.post("/2fa/enroll", response_model=EnrollResponse)
async def enroll_2fa(
    user: AdminUser = Depends(get_current_user_active), session: AsyncSession = Depends(get_session)
) -> EnrollResponse:
    try:
        secret, uri = await TwoFactorService(session).enroll(user)
    except TwoFactorError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await session.commit()
    return EnrollResponse(secret=secret, otpauth_uri=uri)


@router.post("/2fa/confirm", response_model=RecoveryCodesResponse)
async def confirm_2fa(
    payload: TwoFactorCodeRequest,
    user: AdminUser = Depends(get_current_user_active),
    session: AsyncSession = Depends(get_session),
) -> RecoveryCodesResponse:
    try:
        codes = await TwoFactorService(session).confirm(user, payload.code)
    except TwoFactorError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await AuditLogService(session).record(
        AuditEvent.ADMIN_ACTION, actor=user.email, data={"action": "2fa_enabled", "user_id": user.id}
    )
    await session.commit()
    return RecoveryCodesResponse(recovery_codes=codes)


@router.post("/2fa/disable")
async def disable_2fa(
    payload: TwoFactorCodeRequest,
    user: AdminUser = Depends(get_current_user_active),
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        await TwoFactorService(session).disable(user, payload.code)
    except TwoFactorError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await AuditLogService(session).record(
        AuditEvent.ADMIN_ACTION, actor=user.email, data={"action": "2fa_disabled", "user_id": user.id}
    )
    await session.commit()
    return {"two_factor_enabled": False}


@router.post("/2fa/recovery-codes/regenerate", response_model=RecoveryCodesResponse)
async def regenerate_recovery_codes(
    payload: TwoFactorCodeRequest,
    user: AdminUser = Depends(get_current_user_active),
    session: AsyncSession = Depends(get_session),
) -> RecoveryCodesResponse:
    try:
        codes = await TwoFactorService(session).regenerate_recovery_codes(user, payload.code)
    except TwoFactorError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await session.commit()
    return RecoveryCodesResponse(recovery_codes=codes)


@router.post("/dev-bootstrap-super-admin", response_model=UserOut)
async def dev_bootstrap_super_admin(
    payload: BootstrapRequest, session: AsyncSession = Depends(get_session)
) -> AdminUser:
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        validate_password(payload.password)
    except PasswordPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    auth = AuthService(session)
    existing = await auth.get_by_email(payload.email)
    if existing is not None:
        return existing
    user = await auth.create_user(
        email=payload.email, password=payload.password, full_name=payload.full_name, role="super_admin"
    )
    await session.commit()
    return user
