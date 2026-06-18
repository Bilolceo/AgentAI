"""Audit log admin view: RBAC, filters, pagination, ordering, redaction."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app
from app.models.audit_log import AuditLog
from app.services.auth.service import AuthService

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


async def _token(client, db_session, email, role) -> str:
    await AuthService(db_session).create_user(
        email=email, password="rolepass001", full_name=role, role=role
    )
    await db_session.commit()
    r = await client.post(f"{API}/auth/login", json={"email": email, "password": "rolepass001"})
    return r.json()["access_token"]


async def _add_logs(db_session, specs: list[dict]) -> None:
    for s in specs:
        db_session.add(AuditLog(**s))
    await db_session.commit()


# === RBAC ====================================================================
@pytest.mark.asyncio
async def test_super_admin_can_list(client, db_session) -> None:
    token = await _token(client, db_session, "root@clinic.uz", "super_admin")
    assert (await client.get(f"{API}/admin/audit-logs", headers=_b(token))).status_code == 200


@pytest.mark.asyncio
async def test_admin_can_list(client, db_session) -> None:
    token = await _token(client, db_session, "admin@clinic.uz", "admin")
    assert (await client.get(f"{API}/admin/audit-logs", headers=_b(token))).status_code == 200


@pytest.mark.asyncio
async def test_operator_forbidden(client, db_session) -> None:
    token = await _token(client, db_session, "op@clinic.uz", "operator")
    assert (await client.get(f"{API}/admin/audit-logs", headers=_b(token))).status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_401(client) -> None:
    assert (await client.get(f"{API}/admin/audit-logs")).status_code == 401


# === Filters / pagination / ordering ========================================
@pytest.mark.asyncio
async def test_filter_by_event_type(client, db_session) -> None:
    token = await _token(client, db_session, "admin@clinic.uz", "admin")
    await _add_logs(db_session, [
        {"event": "login_success", "actor": "a@x", "actor_user_id": 1},
        {"event": "user_created", "actor": "a@x", "actor_user_id": 1},
    ])
    r = await client.get(f"{API}/admin/audit-logs", headers=_b(token), params={"event_type": "user_created"})
    events = [row["event_type"] for row in r.json()]
    assert events and all(e == "user_created" for e in events)


@pytest.mark.asyncio
async def test_filter_by_actor_user_id(client, db_session) -> None:
    token = await _token(client, db_session, "admin@clinic.uz", "admin")
    await _add_logs(db_session, [
        {"event": "user_updated", "actor": "a", "actor_user_id": 7},
        {"event": "user_updated", "actor": "b", "actor_user_id": 8},
    ])
    r = await client.get(f"{API}/admin/audit-logs", headers=_b(token), params={"actor_user_id": 7})
    assert all(row["actor_user_id"] == 7 for row in r.json())
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_pagination_and_ordering(client, db_session) -> None:
    token = await _token(client, db_session, "admin@clinic.uz", "admin")
    await _add_logs(db_session, [
        {"event": f"evt_{i}", "actor": "a", "actor_user_id": 99} for i in range(5)
    ])
    rows = (await client.get(
        f"{API}/admin/audit-logs", headers=_b(token), params={"actor_user_id": 99, "limit": 2, "offset": 0}
    )).json()
    assert len(rows) == 2
    # newest first: ids strictly descending
    assert rows[0]["id"] > rows[1]["id"]

    page2 = (await client.get(
        f"{API}/admin/audit-logs", headers=_b(token), params={"actor_user_id": 99, "limit": 2, "offset": 2}
    )).json()
    assert len(page2) == 2
    assert page2[0]["id"] < rows[1]["id"]


# === Redaction ===============================================================
@pytest.mark.asyncio
async def test_sensitive_metadata_redacted(client, db_session) -> None:
    token = await _token(client, db_session, "admin@clinic.uz", "admin")
    await _add_logs(db_session, [{
        "event": "login_success",
        "actor": "x@clinic.uz",
        "actor_user_id": 3,
        "data": {
            "password": "plaintext-should-not-leak",
            "two_factor_secret": "ABCDEF",
            "recovery_codes": ["a", "b"],
            "access_token": "jwt...",
            "reason_code": "operator_request",
            "user_id": 3,
        },
    }])
    row = (await client.get(f"{API}/admin/audit-logs", headers=_b(token))).json()[0]
    md = row["metadata"]
    assert md["password"] == "[REDACTED]"
    assert md["two_factor_secret"] == "[REDACTED]"
    assert md["recovery_codes"] == "[REDACTED]"
    assert md["access_token"] == "[REDACTED]"
    # non-sensitive keys preserved
    assert md["reason_code"] == "operator_request"
    assert md["user_id"] == 3


@pytest.mark.asyncio
async def test_kb_mutation_event_appears(client, db_session) -> None:
    token = await _token(client, db_session, "admin@clinic.uz", "admin")
    await client.post(
        f"{API}/admin/knowledge-items",
        headers=_b(token),
        json={
            "category": "faq", "title": "T", "content_uz": "u", "content_ru": "r",
            "tags": [], "is_active": True,
        },
    )
    r = await client.get(f"{API}/admin/audit-logs", headers=_b(token), params={"event_type": "knowledge_item_created"})
    assert len(r.json()) >= 1
    assert r.json()[0]["actor_user_id"] is not None
