"""Callback task lifecycle: transitions, RBAC, ownership, audit."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app
from app.models.admin_user import AdminUser
from app.models.audit_log import AuditLog
from app.models.call import Call
from app.models.callback_task import CallbackTask
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


async def _user(db_session, email, role) -> AdminUser:
    u = await AuthService(db_session).create_user(
        email=email, password="rolepass001", full_name=role, role=role
    )
    await db_session.commit()
    return u


async def _token(client, email) -> str:
    r = await client.post(f"{API}/auth/login", json={"email": email, "password": "rolepass001"})
    return r.json()["access_token"]


async def _make_callback(db_session, *, status="callback_required", assigned_to=None) -> CallbackTask:
    call = Call(
        twilio_call_sid=f"sim-{uuid.uuid4().hex[:8]}",
        from_number="+998901112233",
        to_number="clinic",
        status="transferred",
    )
    db_session.add(call)
    await db_session.flush()
    cb = CallbackTask(
        call_session_id=call.id,
        patient_phone="+998901112233",
        reason="complaint",
        priority="high",
        status=status,
        assigned_to_user_id=assigned_to,
    )
    db_session.add(cb)
    await db_session.commit()
    return cb


# === assign / complete ======================================================
@pytest.mark.asyncio
async def test_admin_can_assign(client, db_session) -> None:
    admin = await _user(db_session, "admin@clinic.uz", "admin")
    token = await _token(client, "admin@clinic.uz")
    cb = await _make_callback(db_session)
    r = await client.post(f"{API}/admin/callbacks/{cb.id}/assign", headers=_b(token))
    assert r.status_code == 200
    assert r.json()["status"] == "assigned"
    assert r.json()["assigned_to_user_id"] == admin.id


@pytest.mark.asyncio
async def test_operator_can_assign_unassigned_to_self(client, db_session) -> None:
    op = await _user(db_session, "op@clinic.uz", "operator")
    token = await _token(client, "op@clinic.uz")
    cb = await _make_callback(db_session)
    r = await client.post(f"{API}/admin/callbacks/{cb.id}/assign", headers=_b(token))
    assert r.status_code == 200
    assert r.json()["assigned_to_user_id"] == op.id


@pytest.mark.asyncio
async def test_operator_cannot_complete_others_callback(client, db_session) -> None:
    admin = await _user(db_session, "admin@clinic.uz", "admin")
    await _user(db_session, "op@clinic.uz", "operator")
    op_token = await _token(client, "op@clinic.uz")
    cb = await _make_callback(db_session, status="assigned", assigned_to=admin.id)
    r = await client.post(f"{API}/admin/callbacks/{cb.id}/complete", headers=_b(op_token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_operator_can_complete_own_callback(client, db_session) -> None:
    op = await _user(db_session, "op@clinic.uz", "operator")
    token = await _token(client, "op@clinic.uz")
    cb = await _make_callback(db_session, status="assigned", assigned_to=op.id)
    r = await client.post(f"{API}/admin/callbacks/{cb.id}/complete", headers=_b(token))
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert r.json()["completed_at"] is not None


# === cancel / terminal ======================================================
@pytest.mark.asyncio
async def test_admin_can_cancel(client, db_session) -> None:
    await _user(db_session, "admin@clinic.uz", "admin")
    token = await _token(client, "admin@clinic.uz")
    cb = await _make_callback(db_session)
    r = await client.post(f"{API}/admin/callbacks/{cb.id}/cancel", headers=_b(token))
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_completed_callback_cannot_be_modified(client, db_session) -> None:
    op = await _user(db_session, "op@clinic.uz", "operator")
    await _user(db_session, "admin@clinic.uz", "admin")
    op_token = await _token(client, "op@clinic.uz")
    admin_token = await _token(client, "admin@clinic.uz")
    cb = await _make_callback(db_session, status="assigned", assigned_to=op.id)
    assert (await client.post(f"{API}/admin/callbacks/{cb.id}/complete", headers=_b(op_token))).status_code == 200
    # terminal: cancel and notes both rejected
    assert (await client.post(f"{API}/admin/callbacks/{cb.id}/cancel", headers=_b(admin_token))).status_code == 400
    assert (await client.patch(f"{API}/admin/callbacks/{cb.id}/notes", headers=_b(admin_token), json={"resolution_notes": "x"})).status_code == 400


# === reschedule / notes =====================================================
@pytest.mark.asyncio
async def test_reschedule_updates_due_at(client, db_session) -> None:
    await _user(db_session, "admin@clinic.uz", "admin")
    token = await _token(client, "admin@clinic.uz")
    cb = await _make_callback(db_session)
    r = await client.post(
        f"{API}/admin/callbacks/{cb.id}/reschedule",
        headers=_b(token),
        json={"due_at": "2026-08-01T10:00:00+00:00"},
    )
    assert r.status_code == 200
    assert r.json()["due_at"].startswith("2026-08-01")
    assert r.json()["rescheduled_at"] is not None


@pytest.mark.asyncio
async def test_notes_update_is_audited(client, db_session) -> None:
    op = await _user(db_session, "op@clinic.uz", "operator")
    token = await _token(client, "op@clinic.uz")
    cb = await _make_callback(db_session, status="assigned", assigned_to=op.id)
    r = await client.patch(
        f"{API}/admin/callbacks/{cb.id}/notes", headers=_b(token), json={"resolution_notes": "called back, resolved"}
    )
    assert r.status_code == 200
    assert r.json()["resolution_notes"] == "called back, resolved"
    events = set((await db_session.execute(select(AuditLog.event))).scalars().all())
    assert "callback_notes_updated" in events


# === filters / RBAC =========================================================
@pytest.mark.asyncio
async def test_list_assigned_to_me(client, db_session) -> None:
    op = await _user(db_session, "op@clinic.uz", "operator")
    token = await _token(client, "op@clinic.uz")
    mine = await _make_callback(db_session, status="assigned", assigned_to=op.id)
    await _make_callback(db_session)  # unassigned, not mine

    r = await client.get(f"{API}/admin/callbacks", headers=_b(token), params={"assigned_to_me": True})
    assert r.status_code == 200
    ids = [c["id"] for c in r.json()]
    assert ids == [mine.id]


@pytest.mark.asyncio
async def test_rbac_cases(client, db_session) -> None:
    await _user(db_session, "op@clinic.uz", "operator")
    op_token = await _token(client, "op@clinic.uz")
    cb = await _make_callback(db_session)

    # no token -> 401
    assert (await client.get(f"{API}/admin/callbacks")).status_code == 401
    # operator cannot cancel or reschedule -> 403
    assert (await client.post(f"{API}/admin/callbacks/{cb.id}/cancel", headers=_b(op_token))).status_code == 403
    assert (
        await client.post(
            f"{API}/admin/callbacks/{cb.id}/reschedule",
            headers=_b(op_token),
            json={"due_at": "2026-08-01T10:00:00+00:00"},
        )
    ).status_code == 403
