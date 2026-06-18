"""A6.4 auth hardening: token_version, password policy, forced change, lockout."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app
from app.services.auth.attempts import set_clock
from app.services.auth.service import AuthService
from app.services.auth.totp import totp_now

API = "/api/v1"
STRONG = "Userpass001"


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


async def _super(client, db_session):
    await AuthService(db_session).create_user(
        email="root@clinic.uz", password="rootpw0001", full_name="Root", role="super_admin"
    )
    await db_session.commit()
    r = await client.post(f"{API}/auth/login", json={"email": "root@clinic.uz", "password": "rootpw0001"})
    return r.json()["access_token"]


async def _create_user(client, super_token, email, role="admin", *, force=False, password=STRONG):
    r = await client.post(
        f"{API}/admin/users",
        headers=_b(super_token),
        json={"email": email, "full_name": "U", "role": role, "password": password, "force_password_change": force},
    )
    return r


# === token_version =========================================================
@pytest.mark.asyncio
async def test_token_works_before_bump(client, db_session) -> None:
    st = await _super(client, db_session)
    await _create_user(client, st, "u1@clinic.uz")
    token = (await client.post(f"{API}/auth/login", json={"email": "u1@clinic.uz", "password": STRONG})).json()["access_token"]
    assert (await client.get(f"{API}/auth/me", headers=_b(token))).status_code == 200


@pytest.mark.asyncio
async def test_old_token_fails_after_password_reset(client, db_session) -> None:
    st = await _super(client, db_session)
    uid = (await _create_user(client, st, "u2@clinic.uz")).json()["id"]
    token = (await client.post(f"{API}/auth/login", json={"email": "u2@clinic.uz", "password": STRONG})).json()["access_token"]
    await client.post(f"{API}/admin/users/{uid}/reset-password", headers=_b(st), json={"new_password": "Brandnew001"})
    assert (await client.get(f"{API}/auth/me", headers=_b(token))).status_code == 401


@pytest.mark.asyncio
async def test_old_token_fails_after_deactivate(client, db_session) -> None:
    st = await _super(client, db_session)
    uid = (await _create_user(client, st, "u3@clinic.uz")).json()["id"]
    token = (await client.post(f"{API}/auth/login", json={"email": "u3@clinic.uz", "password": STRONG})).json()["access_token"]
    await client.post(f"{API}/admin/users/{uid}/deactivate", headers=_b(st))
    assert (await client.get(f"{API}/auth/me", headers=_b(token))).status_code == 401


@pytest.mark.asyncio
async def test_old_token_fails_after_2fa_reset(client, db_session) -> None:
    st = await _super(client, db_session)
    uid = (await _create_user(client, st, "u4@clinic.uz")).json()["id"]
    token = (await client.post(f"{API}/auth/login", json={"email": "u4@clinic.uz", "password": STRONG})).json()["access_token"]
    await client.post(f"{API}/admin/users/{uid}/reset-2fa", headers=_b(st))
    assert (await client.get(f"{API}/auth/me", headers=_b(token))).status_code == 401


# === password policy ========================================================
@pytest.mark.asyncio
async def test_weak_password_rejected_on_create(client, db_session) -> None:
    st = await _super(client, db_session)
    r = await _create_user(client, st, "weak1@clinic.uz", password="short")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_weak_password_rejected_on_reset(client, db_session) -> None:
    st = await _super(client, db_session)
    uid = (await _create_user(client, st, "weak2@clinic.uz")).json()["id"]
    r = await client.post(f"{API}/admin/users/{uid}/reset-password", headers=_b(st), json={"new_password": "nodigitsxx"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_weak_password_rejected_on_bootstrap(client) -> None:
    r = await client.post(
        f"{API}/auth/dev-bootstrap-super-admin",
        json={"email": "weakboot@clinic.uz", "password": "short", "full_name": "B"},
    )
    assert r.status_code == 400


# === forced password change =================================================
@pytest.mark.asyncio
async def test_force_password_change_flow(client, db_session) -> None:
    st = await _super(client, db_session)
    await _create_user(client, st, "fp@clinic.uz", role="admin", force=True)
    token = (await client.post(f"{API}/auth/login", json={"email": "fp@clinic.uz", "password": STRONG})).json()["access_token"]

    # blocked from admin endpoints
    blocked = await client.get(f"{API}/admin/stats", headers=_b(token))
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "password_change_required"

    # but /auth/me works and exposes the flag
    me = await client.get(f"{API}/auth/me", headers=_b(token))
    assert me.status_code == 200
    assert me.json()["force_password_change"] is True

    # change password clears the flag and bumps token_version
    changed = await client.post(
        f"{API}/auth/change-password",
        headers=_b(token),
        json={"old_password": STRONG, "new_password": "Changed0001"},
    )
    assert changed.status_code == 200
    # old token now invalid (version bump)
    assert (await client.get(f"{API}/auth/me", headers=_b(token))).status_code == 401

    # re-login: flag cleared, admin endpoints reachable
    new_token = (await client.post(f"{API}/auth/login", json={"email": "fp@clinic.uz", "password": "Changed0001"})).json()["access_token"]
    me2 = await client.get(f"{API}/auth/me", headers=_b(new_token))
    assert me2.json()["force_password_change"] is False
    assert (await client.get(f"{API}/admin/stats", headers=_b(new_token))).status_code == 200


# === lockout ================================================================
@pytest.mark.asyncio
async def test_login_lockout_after_repeated_failures(client, db_session) -> None:
    clock = {"t": 1000.0}
    set_clock(lambda: clock["t"])
    st = await _super(client, db_session)
    await _create_user(client, st, "lock@clinic.uz")

    for _ in range(5):
        r = await client.post(f"{API}/auth/login", json={"email": "lock@clinic.uz", "password": "WrongPass999"})
        assert r.status_code == 401
    # now locked
    locked = await client.post(f"{API}/auth/login", json={"email": "lock@clinic.uz", "password": STRONG})
    assert locked.status_code == 423

    # after the lock window passes, login works again
    clock["t"] += 16 * 60
    ok = await client.post(f"{API}/auth/login", json={"email": "lock@clinic.uz", "password": STRONG})
    assert ok.status_code == 200


@pytest.mark.asyncio
async def test_2fa_lockout_after_repeated_bad_codes(client, db_session) -> None:
    clock = {"t": 2000.0}
    set_clock(lambda: clock["t"])
    st = await _super(client, db_session)
    await _create_user(client, st, "tf@clinic.uz")
    user_token = (await client.post(f"{API}/auth/login", json={"email": "tf@clinic.uz", "password": STRONG})).json()["access_token"]
    secret = (await client.post(f"{API}/auth/2fa/enroll", headers=_b(user_token))).json()["secret"]
    await client.post(f"{API}/auth/2fa/confirm", json={"code": totp_now(secret)}, headers=_b(user_token))

    ticket = (await client.post(f"{API}/auth/login", json={"email": "tf@clinic.uz", "password": STRONG})).json()["two_factor_ticket"]
    for _ in range(5):
        bad = await client.post(f"{API}/auth/login/2fa", json={"code": "000000"}, headers=_b(ticket))
        assert bad.status_code == 401
    locked = await client.post(f"{API}/auth/login/2fa", json={"code": "000000"}, headers=_b(ticket))
    assert locked.status_code == 423


@pytest.mark.asyncio
async def test_successful_login_clears_failures(client, db_session) -> None:
    clock = {"t": 3000.0}
    set_clock(lambda: clock["t"])
    st = await _super(client, db_session)
    await _create_user(client, st, "clear@clinic.uz")

    for _ in range(4):
        assert (await client.post(f"{API}/auth/login", json={"email": "clear@clinic.uz", "password": "WrongPass999"})).status_code == 401
    assert (await client.post(f"{API}/auth/login", json={"email": "clear@clinic.uz", "password": STRONG})).status_code == 200
    # counter reset -> 4 more bad attempts still do not lock
    for _ in range(4):
        r = await client.post(f"{API}/auth/login", json={"email": "clear@clinic.uz", "password": "WrongPass999"})
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_no_sensitive_values_serialized(client, db_session) -> None:
    st = await _super(client, db_session)
    created = (await _create_user(client, st, "ser@clinic.uz")).json()
    token = (await client.post(f"{API}/auth/login", json={"email": "ser@clinic.uz", "password": STRONG})).json()["access_token"]
    me = (await client.get(f"{API}/auth/me", headers=_b(token))).json()
    for blob in (created, me):
        assert "password_hash" not in blob
        assert "two_factor_secret" not in blob
        assert "two_factor_recovery_codes" not in blob
        assert "token_version" not in blob
