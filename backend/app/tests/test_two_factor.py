"""TOTP 2FA tests: enroll, confirm, 2-step login, recovery codes, disable."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app
from app.services.auth.service import AuthService
from app.services.auth.totp import totp_now

API = "/api/v1"


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _login_token(client: AsyncClient, email: str, password: str) -> str:
    r = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


async def _enable_2fa(client: AsyncClient, db_session, email="u@clinic.uz", password="pw"):
    await AuthService(db_session).create_user(
        email=email, password=password, full_name="U", role="admin"
    )
    await db_session.commit()
    token = await _login_token(client, email, password)
    secret = (await client.post(f"{API}/auth/2fa/enroll", headers=_bearer(token))).json()["secret"]
    r = await client.post(f"{API}/auth/2fa/confirm", json={"code": totp_now(secret)}, headers=_bearer(token))
    codes = r.json()["recovery_codes"]
    return secret, codes, token, email, password


@pytest.mark.asyncio
async def test_enroll_confirm_and_totp_login(client, db_session) -> None:
    secret, codes, _token, email, pw = await _enable_2fa(client, db_session)
    assert len(codes) == 10

    r = await client.post(f"{API}/auth/login", json={"email": email, "password": pw})
    body = r.json()
    assert body["two_factor_required"] is True
    assert body["access_token"] is None
    ticket = body["two_factor_ticket"]

    r2 = await client.post(f"{API}/auth/login/2fa", json={"code": totp_now(secret)}, headers=_bearer(ticket))
    assert r2.status_code == 200
    assert r2.json()["access_token"]


@pytest.mark.asyncio
async def test_recovery_code_login_is_single_use(client, db_session) -> None:
    _secret, codes, _token, email, pw = await _enable_2fa(client, db_session)

    ticket = (await client.post(f"{API}/auth/login", json={"email": email, "password": pw})).json()["two_factor_ticket"]
    ok = await client.post(f"{API}/auth/login/2fa", json={"code": codes[0]}, headers=_bearer(ticket))
    assert ok.status_code == 200

    ticket2 = (await client.post(f"{API}/auth/login", json={"email": email, "password": pw})).json()["two_factor_ticket"]
    reused = await client.post(f"{API}/auth/login/2fa", json={"code": codes[0]}, headers=_bearer(ticket2))
    assert reused.status_code == 401


@pytest.mark.asyncio
async def test_two_factor_ticket_cannot_access_admin(client, db_session) -> None:
    _secret, _codes, _token, email, pw = await _enable_2fa(client, db_session)
    ticket = (await client.post(f"{API}/auth/login", json={"email": email, "password": pw})).json()["two_factor_ticket"]
    r = await client.get(f"{API}/admin/stats", headers=_bearer(ticket))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_wrong_2fa_code_rejected(client, db_session) -> None:
    _secret, _codes, _token, email, pw = await _enable_2fa(client, db_session)
    ticket = (await client.post(f"{API}/auth/login", json={"email": email, "password": pw})).json()["two_factor_ticket"]
    r = await client.post(f"{API}/auth/login/2fa", json={"code": "000000"}, headers=_bearer(ticket))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_disable_2fa(client, db_session) -> None:
    secret, _codes, token, email, pw = await _enable_2fa(client, db_session)
    r = await client.post(f"{API}/auth/2fa/disable", json={"code": totp_now(secret)}, headers=_bearer(token))
    assert r.status_code == 200
    assert r.json()["two_factor_enabled"] is False

    # login no longer requires 2FA
    body = (await client.post(f"{API}/auth/login", json={"email": email, "password": pw})).json()
    assert body["two_factor_required"] is False
    assert body["access_token"]


@pytest.mark.asyncio
async def test_regenerate_recovery_codes_invalidates_old(client, db_session) -> None:
    secret, old_codes, token, email, pw = await _enable_2fa(client, db_session)
    new_codes = (
        await client.post(
            f"{API}/auth/2fa/recovery-codes/regenerate",
            json={"code": totp_now(secret)},
            headers=_bearer(token),
        )
    ).json()["recovery_codes"]
    assert set(new_codes).isdisjoint(set(old_codes))

    ticket = (await client.post(f"{API}/auth/login", json={"email": email, "password": pw})).json()["two_factor_ticket"]
    old = await client.post(f"{API}/auth/login/2fa", json={"code": old_codes[0]}, headers=_bearer(ticket))
    assert old.status_code == 401

    ticket2 = (await client.post(f"{API}/auth/login", json={"email": email, "password": pw})).json()["two_factor_ticket"]
    new = await client.post(f"{API}/auth/login/2fa", json={"code": new_codes[0]}, headers=_bearer(ticket2))
    assert new.status_code == 200


@pytest.mark.asyncio
async def test_enroll_when_already_enabled_400(client, db_session) -> None:
    _secret, _codes, token, _email, _pw = await _enable_2fa(client, db_session)
    r = await client.post(f"{API}/auth/2fa/enroll", headers=_bearer(token))
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_secret_and_recovery_not_serialized(client, db_session) -> None:
    _secret, _codes, token, _email, _pw = await _enable_2fa(client, db_session)
    me = (await client.get(f"{API}/auth/me", headers=_bearer(token))).json()
    assert me["two_factor_enabled"] is True
    assert "two_factor_secret" not in me
    assert "two_factor_recovery_codes" not in me
    assert "password_hash" not in me
