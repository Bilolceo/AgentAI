"""Admin user-management tests (RBAC, safety invariants, audit)."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app
from app.models.admin_user import AdminUser
from app.models.audit_log import AuditLog
from app.services.auth.service import AuthService
from app.services.auth.totp import totp_now
from app.services.auth.user_management import LastSuperAdminError, UserManagementService

API = "/api/v1"


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def _b(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _make(db_session, email, password, role, *, active=True) -> None:
    await AuthService(db_session).create_user(
        email=email, password=password, full_name=role, role=role, is_active=active
    )
    await db_session.commit()


async def _token(client, email, password) -> str:
    r = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


async def _super(client, db_session):
    await _make(db_session, "root@clinic.uz", "rootpw", "super_admin")
    token = await _token(client, "root@clinic.uz", "rootpw")
    me = (await client.get(f"{API}/auth/me", headers=_b(token))).json()
    return token, me["id"]


# === RBAC ====================================================================
@pytest.mark.asyncio
async def test_super_admin_can_create_user(client, db_session) -> None:
    token, _ = await _super(client, db_session)
    r = await client.post(
        f"{API}/admin/users",
        headers=_b(token),
        json={"email": "op1@clinic.uz", "full_name": "Op", "role": "operator", "password": "Userpass001"},
    )
    assert r.status_code == 201
    assert r.json()["role"] == "operator"
    assert "password_hash" not in r.json()


@pytest.mark.asyncio
async def test_admin_cannot_create_user(client, db_session) -> None:
    await _make(db_session, "admin@clinic.uz", "Userpass001", "admin")
    token = await _token(client, "admin@clinic.uz", "Userpass001")
    r = await client.post(
        f"{API}/admin/users",
        headers=_b(token),
        json={"email": "x@clinic.uz", "full_name": "X", "role": "operator", "password": "Userpass001"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_operator_cannot_list_users(client, db_session) -> None:
    await _make(db_session, "op@clinic.uz", "Userpass001", "operator")
    token = await _token(client, "op@clinic.uz", "Userpass001")
    r = await client.get(f"{API}/admin/users", headers=_b(token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_list_users(client, db_session) -> None:
    await _make(db_session, "admin@clinic.uz", "Userpass001", "admin")
    token = await _token(client, "admin@clinic.uz", "Userpass001")
    r = await client.get(f"{API}/admin/users", headers=_b(token))
    assert r.status_code == 200


# === Safety / validation =====================================================
@pytest.mark.asyncio
async def test_email_uniqueness(client, db_session) -> None:
    token, _ = await _super(client, db_session)
    body = {"email": "dup@clinic.uz", "full_name": "D", "role": "operator", "password": "Userpass001"}
    assert (await client.post(f"{API}/admin/users", headers=_b(token), json=body)).status_code == 201
    assert (await client.post(f"{API}/admin/users", headers=_b(token), json=body)).status_code == 409


@pytest.mark.asyncio
async def test_password_hash_and_2fa_secret_not_returned(client, db_session) -> None:
    token, _ = await _super(client, db_session)
    created = (
        await client.post(
            f"{API}/admin/users",
            headers=_b(token),
            json={"email": "p@clinic.uz", "full_name": "P", "role": "admin", "password": "Userpass001"},
        )
    ).json()
    got = (await client.get(f"{API}/admin/users/{created['id']}", headers=_b(token))).json()
    for blob in (created, got):
        assert "password_hash" not in blob
        assert "two_factor_secret" not in blob
        assert "two_factor_recovery_codes" not in blob


@pytest.mark.asyncio
async def test_cannot_deactivate_self(client, db_session) -> None:
    token, my_id = await _super(client, db_session)
    r = await client.post(f"{API}/admin/users/{my_id}/deactivate", headers=_b(token))
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_cannot_deactivate_last_super_admin_service(db_session) -> None:
    user = await AuthService(db_session).create_user(
        email="solo@clinic.uz", password="Userpass001", full_name="Solo", role="super_admin"
    )
    await db_session.commit()
    svc = UserManagementService(db_session)
    with pytest.raises(LastSuperAdminError):
        await svc.deactivate(user.id, actor_id=999999)


@pytest.mark.asyncio
async def test_cannot_demote_last_super_admin(client, db_session) -> None:
    token, my_id = await _super(client, db_session)
    r = await client.patch(f"{API}/admin/users/{my_id}", headers=_b(token), json={"role": "admin"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_demote_allowed_when_another_super_admin_exists(client, db_session) -> None:
    token, _ = await _super(client, db_session)
    other = (
        await client.post(
            f"{API}/admin/users",
            headers=_b(token),
            json={"email": "s2@clinic.uz", "full_name": "S2", "role": "super_admin", "password": "Userpass001"},
        )
    ).json()
    r = await client.patch(f"{API}/admin/users/{other['id']}", headers=_b(token), json={"role": "admin"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


# === Reset password / 2FA ====================================================
@pytest.mark.asyncio
async def test_reset_password_changes_login(client, db_session) -> None:
    token, _ = await _super(client, db_session)
    user = (
        await client.post(
            f"{API}/admin/users",
            headers=_b(token),
            json={"email": "u@clinic.uz", "full_name": "U", "role": "admin", "password": "OldPassw0rd1"},
        )
    ).json()
    r = await client.post(
        f"{API}/admin/users/{user['id']}/reset-password",
        headers=_b(token),
        json={"new_password": "NewPassw0rd1"},
    )
    assert r.status_code == 200
    assert (await client.post(f"{API}/auth/login", json={"email": "u@clinic.uz", "password": "OldPassw0rd1"})).status_code == 401
    assert (await client.post(f"{API}/auth/login", json={"email": "u@clinic.uz", "password": "NewPassw0rd1"})).status_code == 200


@pytest.mark.asyncio
async def test_reset_2fa_clears_fields(client, db_session) -> None:
    token, _ = await _super(client, db_session)
    user = (
        await client.post(
            f"{API}/admin/users",
            headers=_b(token),
            json={"email": "tfa@clinic.uz", "full_name": "T", "role": "admin", "password": "Userpass001"},
        )
    ).json()
    # The user enables 2FA themselves.
    user_token = await _token(client, "tfa@clinic.uz", "Userpass001")
    secret = (await client.post(f"{API}/auth/2fa/enroll", headers=_b(user_token))).json()["secret"]
    await client.post(f"{API}/auth/2fa/confirm", json={"code": totp_now(secret)}, headers=_b(user_token))

    # super_admin resets it.
    r = await client.post(f"{API}/admin/users/{user['id']}/reset-2fa", headers=_b(token))
    assert r.status_code == 200
    assert r.json()["two_factor_enabled"] is False

    # Login no longer requires 2FA.
    body = (await client.post(f"{API}/auth/login", json={"email": "tfa@clinic.uz", "password": "Userpass001"})).json()
    assert body["two_factor_required"] is False
    assert body["access_token"]

    stored = await db_session.get(AdminUser, user["id"])
    assert stored.two_factor_secret is None
    assert stored.two_factor_recovery_codes is None


# === Inactive token + audit ==================================================
@pytest.mark.asyncio
async def test_inactive_user_old_token_cannot_access(client, db_session) -> None:
    token, _ = await _super(client, db_session)
    user = (
        await client.post(
            f"{API}/admin/users",
            headers=_b(token),
            json={"email": "z@clinic.uz", "full_name": "Z", "role": "admin", "password": "Userpass001"},
        )
    ).json()
    user_token = await _token(client, "z@clinic.uz", "Userpass001")
    assert (await client.get(f"{API}/auth/me", headers=_b(user_token))).status_code == 200

    await client.post(f"{API}/admin/users/{user['id']}/deactivate", headers=_b(token))
    assert (await client.get(f"{API}/auth/me", headers=_b(user_token))).status_code == 401


@pytest.mark.asyncio
async def test_audit_events_for_mutations(client, db_session) -> None:
    token, _ = await _super(client, db_session)
    user = (
        await client.post(
            f"{API}/admin/users",
            headers=_b(token),
            json={"email": "a@clinic.uz", "full_name": "A", "role": "operator", "password": "Userpass001"},
        )
    ).json()
    await client.post(f"{API}/admin/users/{user['id']}/deactivate", headers=_b(token))

    events = set(
        (await db_session.execute(select(AuditLog.event))).scalars().all()
    )
    assert "user_created" in events
    assert "user_deactivated" in events
