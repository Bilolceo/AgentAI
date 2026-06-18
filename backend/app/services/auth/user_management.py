"""UserManagementService — super_admin management of admin users (TZ §8.5).

Safety invariants (cannot deactivate/demote the last active super_admin, cannot
deactivate yourself, unique email) live here so they hold regardless of caller.
Role-based access (who may call) is enforced by endpoint dependencies.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.services.auth.password import hash_password, validate_password
from app.services.auth.service import VALID_ROLES, AuthService


class UserManagementError(Exception):
    """Base class for user-management rule violations (-> HTTP 400)."""


class EmailExistsError(UserManagementError):
    """Email already in use (-> HTTP 409)."""


class LastSuperAdminError(UserManagementError):
    """Would remove the last active super_admin (-> HTTP 400)."""


class SelfActionError(UserManagementError):
    """Actor attempted a forbidden action on themselves (-> HTTP 400)."""


class UserNotFoundError(UserManagementError):
    """Target user does not exist (-> HTTP 404)."""


class UserManagementService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._auth = AuthService(session)

    async def list_users(self) -> list[AdminUser]:
        rows = await self._session.execute(select(AdminUser).order_by(AdminUser.id))
        return list(rows.scalars())

    async def get(self, user_id: int) -> Optional[AdminUser]:
        return await self._auth.get_by_id(user_id)

    async def _require(self, user_id: int) -> AdminUser:
        user = await self._auth.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"user {user_id} not found")
        return user

    async def _active_super_admin_count(self) -> int:
        stmt = (
            select(func.count())
            .select_from(AdminUser)
            .where(AdminUser.role == "super_admin", AdminUser.is_active.is_(True))
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def create(
        self,
        *,
        email: str,
        full_name: Optional[str],
        role: str,
        password: str,
        is_active: bool = True,
        force_password_change: bool = False,
    ) -> AdminUser:
        if role not in VALID_ROLES:
            raise UserManagementError(f"invalid role: {role}")
        validate_password(password)  # raises PasswordPolicyError on weak input
        if await self._auth.get_by_email(email) is not None:
            raise EmailExistsError("email already in use")
        user = await self._auth.create_user(
            email=email, password=password, full_name=full_name, role=role, is_active=is_active
        )
        user.force_password_change = force_password_change
        await self._session.flush()
        return user

    async def update(
        self, target_id: int, *, full_name: Optional[str] = None, role: Optional[str] = None
    ) -> AdminUser:
        user = await self._require(target_id)
        if role is not None and role != user.role:
            if role not in VALID_ROLES:
                raise UserManagementError(f"invalid role: {role}")
            if (
                user.role == "super_admin"
                and user.is_active
                and role != "super_admin"
                and await self._active_super_admin_count() == 1
            ):
                raise LastSuperAdminError("cannot demote the last active super_admin")
            user.role = role
            user.token_version += 1  # role change revokes existing tokens
        if full_name is not None:
            user.full_name = full_name
        await self._session.flush()
        return user

    async def activate(self, target_id: int) -> AdminUser:
        user = await self._require(target_id)
        user.is_active = True
        await self._session.flush()
        return user

    async def deactivate(self, target_id: int, *, actor_id: int) -> AdminUser:
        if target_id == actor_id:
            raise SelfActionError("cannot deactivate yourself")
        user = await self._require(target_id)
        if (
            user.role == "super_admin"
            and user.is_active
            and await self._active_super_admin_count() == 1
        ):
            raise LastSuperAdminError("cannot deactivate the last active super_admin")
        user.is_active = False
        user.token_version += 1  # revoke existing tokens
        await self._session.flush()
        return user

    async def reset_password(self, target_id: int, new_password: str) -> AdminUser:
        validate_password(new_password)  # raises PasswordPolicyError on weak input
        user = await self._require(target_id)
        user.password_hash = hash_password(new_password)  # old password stops working
        user.force_password_change = True
        user.token_version += 1  # revoke existing tokens
        await self._session.flush()
        return user

    async def reset_2fa(self, target_id: int) -> AdminUser:
        user = await self._require(target_id)
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_recovery_codes = None
        user.token_version += 1  # revoke existing tokens
        await self._session.flush()
        return user
