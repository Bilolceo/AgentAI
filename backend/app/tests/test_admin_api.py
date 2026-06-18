"""Admin dashboard API tests (in-process ASGI client over the test DB)."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app
from app.models.callback_task import CallbackTask
from app.services.auth.service import AuthService

API = "/api/v1"


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        # Authenticate as a super_admin so the admin endpoints are reachable.
        await AuthService(db_session).create_user(
            email="root@clinic.uz", password="rootpw", full_name="Root", role="super_admin"
        )
        await db_session.commit()
        r = await c.post(f"{API}/auth/login", json={"email": "root@clinic.uz", "password": "rootpw"})
        c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
        yield c
    app.dependency_overrides.clear()


async def _seed_conversation(client: AsyncClient, db_session: AsyncSession) -> int:
    await client.post(f"{API}/admin/knowledge/seed")
    r = await client.post(f"{API}/simulation/calls", json={"from_number": "+998901112233"})
    call_id = r.json()["call_id"]
    # KB-grounded answer (sources) then an explicit operator request (transfer).
    await client.post(f"{API}/simulation/calls/{call_id}/message",
                      json={"text": "Klinika manzili qayerda?"})
    await client.post(f"{API}/simulation/calls/{call_id}/message",
                      json={"text": "Operatorga ulang"})
    # Operator is available in the sim, so add a callback task explicitly.
    db_session.add(CallbackTask(
        call_session_id=call_id, patient_phone="+998901112233",
        reason="complaint", priority="high", status="callback_required",
    ))
    await db_session.commit()
    return call_id


@pytest.mark.asyncio
async def test_admin_stats(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_conversation(client, db_session)
    r = await client.get(f"{API}/admin/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total_calls"] >= 1
    assert body["kb_items"] > 0
    assert body["operator_transfers"] >= 1
    assert body["callbacks_required"] >= 1
    assert len(body["recent_calls"]) >= 1


@pytest.mark.asyncio
async def test_admin_calls_list_and_filter(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_conversation(client, db_session)
    r = await client.get(f"{API}/admin/calls")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    r2 = await client.get(f"{API}/admin/calls", params={"status": "transferred"})
    assert r2.status_code == 200
    assert all(c["status"] == "transferred" for c in r2.json())
    assert len(r2.json()) >= 1


@pytest.mark.asyncio
async def test_admin_call_detail(client: AsyncClient, db_session: AsyncSession) -> None:
    call_id = await _seed_conversation(client, db_session)
    r = await client.get(f"{API}/admin/calls/{call_id}")
    assert r.status_code == 200
    body = r.json()
    # greeting + 2 user + 2 assistant transcripts
    assert len(body["transcripts"]) >= 5
    assert body["transfer"]["reason"] == "explicit_operator_request"
    assert body["sources"]  # KB sources from the address answer
    assert body["callback"]["reason"] == "complaint"
    assert "operator_request" in body["reason_codes"]


@pytest.mark.asyncio
async def test_admin_call_detail_404(client: AsyncClient) -> None:
    r = await client.get(f"{API}/admin/calls/99999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_callbacks(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_conversation(client, db_session)
    r = await client.get(f"{API}/admin/callbacks")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 1
    assert rows[0]["status"] == "callback_required"
    assert rows[0]["priority"] == "high"


@pytest.mark.asyncio
async def test_admin_knowledge_items(client: AsyncClient, db_session: AsyncSession) -> None:
    await client.post(f"{API}/admin/knowledge/seed")
    r = await client.get(f"{API}/admin/knowledge-items", params={"active_only": True})
    assert r.status_code == 200
    items = r.json()
    assert len(items) > 0
    assert all(i["is_active"] for i in items)
