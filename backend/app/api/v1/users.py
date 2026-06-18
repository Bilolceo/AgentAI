"""Admin user management endpoints (TZ §8.5). Logic lives in services.

Reads: super_admin, admin. Mutations: super_admin only.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.admin_user import AdminUser
from app.schemas.users import AdminUserOut, PasswordReset, UserCreate, UserUpdate
from app.services.audit.log import AuditEvent, AuditLogService
from app.services.auth.deps import require_roles
from app.services.auth.password import PasswordPolicyError
from app.services.auth.user_management import (
    EmailExistsError,
    UserManagementError,
    UserManagementService,
    UserNotFoundError,
)

router = APIRouter()

_READERS = require_roles("super_admin", "admin")
_SUPER = require_roles("super_admin")


def _raise(exc: UserManagementError):
    if isinstance(exc, UserNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, EmailExistsError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


async def _audit(
    session: AsyncSession, event: AuditEvent, actor: AdminUser, target_id: int, **extra
) -> None:
    await AuditLogService(session).record(
        event,
        actor=actor.email,
        actor_user_id=actor.id,
        data={"actor_user_id": actor.id, "target_user_id": target_id, **extra},
    )


@router.get("", response_model=list[AdminUserOut])
async def list_users(
    session: AsyncSession = Depends(get_session), _user: AdminUser = Depends(_READERS)
) -> list[AdminUser]:
    return await UserManagementService(session).list_users()


@router.post("", response_model=AdminUserOut, status_code=201)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
    actor: AdminUser = Depends(_SUPER),
) -> AdminUser:
    svc = UserManagementService(session)
    try:
        user = await svc.create(
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role,
            password=payload.password,
            is_active=payload.is_active,
            force_password_change=payload.force_password_change,
        )
    except PasswordPolicyError as exc:
        await AuditLogService(session).record(
            AuditEvent.WEAK_PASSWORD_REJECTED, actor=actor.email, data={"actor_user_id": actor.id}
        )
        await session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UserManagementError as exc:
        _raise(exc)
    await _audit(session, AuditEvent.USER_CREATED, actor, user.id, role=user.role)
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/{user_id}", response_model=AdminUserOut)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    _user: AdminUser = Depends(_READERS),
) -> AdminUser:
    user = await UserManagementService(session).get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_session),
    actor: AdminUser = Depends(_SUPER),
) -> AdminUser:
    svc = UserManagementService(session)
    try:
        user = await svc.update(user_id, full_name=payload.full_name, role=payload.role)
    except UserManagementError as exc:
        _raise(exc)
    await _audit(session, AuditEvent.USER_UPDATED, actor, user.id, role=user.role)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/{user_id}/activate", response_model=AdminUserOut)
async def activate_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    actor: AdminUser = Depends(_SUPER),
) -> AdminUser:
    svc = UserManagementService(session)
    try:
        user = await svc.activate(user_id)
    except UserManagementError as exc:
        _raise(exc)
    await _audit(session, AuditEvent.USER_ACTIVATED, actor, user.id)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/{user_id}/deactivate", response_model=AdminUserOut)
async def deactivate_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    actor: AdminUser = Depends(_SUPER),
) -> AdminUser:
    svc = UserManagementService(session)
    try:
        user = await svc.deactivate(user_id, actor_id=actor.id)
    except UserManagementError as exc:
        _raise(exc)
    await _audit(session, AuditEvent.USER_DEACTIVATED, actor, user.id)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/{user_id}/reset-password", response_model=AdminUserOut)
async def reset_password(
    user_id: int,
    payload: PasswordReset,
    session: AsyncSession = Depends(get_session),
    actor: AdminUser = Depends(_SUPER),
) -> AdminUser:
    svc = UserManagementService(session)
    try:
        user = await svc.reset_password(user_id, payload.new_password)
    except PasswordPolicyError as exc:
        await AuditLogService(session).record(
            AuditEvent.WEAK_PASSWORD_REJECTED, actor=actor.email, data={"actor_user_id": actor.id}
        )
        await session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UserManagementError as exc:
        _raise(exc)
    await _audit(session, AuditEvent.USER_PASSWORD_RESET, actor, user.id)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/{user_id}/reset-2fa", response_model=AdminUserOut)
async def reset_2fa(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    actor: AdminUser = Depends(_SUPER),
) -> AdminUser:
    svc = UserManagementService(session)
    try:
        user = await svc.reset_2fa(user_id)
    except UserManagementError as exc:
        _raise(exc)
    await _audit(session, AuditEvent.USER_2FA_RESET, actor, user.id)
    await session.commit()
    await session.refresh(user)
    return user
