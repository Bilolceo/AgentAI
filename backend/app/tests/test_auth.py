"""Auth + RBAC tests (in-process ASGI client over the test DB)."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app
from app.services.auth.service import AuthService

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


async def _make_user(db_session, email, password, role, *, active=True) -> None:
    await AuthService(db_session).create_user(
        email=email, password=password, full_name=role, role=role, is_active=active
    )
    await db_session.commit()


async def _token(client: AsyncClient, email: str, password: str) -> str:
    r = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# === Login ===================================================================
@pytest.mark.asyncio
async def test_login_success(client, db_session) -> None:
    await _make_user(db_session, "admin@clinic.uz", "secret", "admin")
    r = await client.post(f"{API}/auth/login", json={"email": "admin@clinic.uz", "password": "secret"})
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["user"]["role"] == "admin"
    assert "password_hash" not in body["user"]


@pytest.mark.asyncio
async def test_login_invalid_password(client, db_session) -> None:
    await _make_user(db_session, "admin@clinic.uz", "secret", "admin")
    r = await client.post(f"{API}/auth/login", json={"email": "admin@clinic.uz", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_cannot_login(client, db_session) -> None:
    await _make_user(db_session, "ghost@clinic.uz", "secret", "admin", active=False)
    r = await client.post(f"{API}/auth/login", json={"email": "ghost@clinic.uz", "password": "secret"})
    assert r.status_code == 401


# === RBAC on admin endpoints =================================================
@pytest.mark.asyncio
async def test_stats_without_token_401(client) -> None:
    r = await client.get(f"{API}/admin/stats")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_stats_with_admin_token_200(client, db_session) -> None:
    await _make_user(db_session, "admin@clinic.uz", "secret", "admin")
    token = await _token(client, "admin@clinic.uz", "secret")
    r = await client.get(f"{API}/admin/stats", headers=_bearer(token))
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_seed_with_admin_token_403(client, db_session) -> None:
    await _make_user(db_session, "admin@clinic.uz", "secret", "admin")
    token = await _token(client, "admin@clinic.uz", "secret")
    r = await client.post(f"{API}/admin/knowledge/seed", headers=_bearer(token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_seed_with_super_admin_token_200(client, db_session) -> None:
    await _make_user(db_session, "root@clinic.uz", "secret", "super_admin")
    token = await _token(client, "root@clinic.uz", "secret")
    r = await client.post(f"{API}/admin/knowledge/seed", headers=_bearer(token))
    assert r.status_code == 200
    assert r.json()["inserted"] > 0


@pytest.mark.asyncio
async def test_operator_can_read_calls_but_not_kb(client, db_session) -> None:
    await _make_user(db_session, "op@clinic.uz", "secret", "operator")
    token = await _token(client, "op@clinic.uz", "secret")
    assert (await client.get(f"{API}/admin/calls", headers=_bearer(token))).status_code == 200
    assert (await client.get(f"{API}/admin/knowledge-items", headers=_bearer(token))).status_code == 403


@pytest.mark.asyncio
async def test_password_hash_not_returned(client, db_session) -> None:
    await _make_user(db_session, "admin@clinic.uz", "secret", "admin")
    token = await _token(client, "admin@clinic.uz", "secret")
    r = await client.get(f"{API}/auth/me", headers=_bearer(token))
    assert r.status_code == 200
    assert "password_hash" not in r.json()


@pytest.mark.asyncio
async def test_invalid_token_401(client) -> None:
    r = await client.get(f"{API}/auth/me", headers=_bearer("not.a.token"))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_dev_bootstrap_super_admin(client) -> None:
    r = await client.post(
        f"{API}/auth/dev-bootstrap-super-admin",
        json={"email": "boot@clinic.uz", "password": "Boot1passwd", "full_name": "Boot"},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "super_admin"
    assert "password_hash" not in r.json()
