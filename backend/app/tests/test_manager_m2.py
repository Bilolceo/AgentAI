"""M2 - doctors + appointments (manager schedule/reports). Role-gated, masked."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app
from app.services.auth.service import AuthService
from app.services.clinic.service import short_name

API = "/api/v1"


async def _login(c: AsyncClient, email: str, password: str) -> None:
    r = await c.post(f"{API}/auth/login", json={"email": email, "password": password})
    c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"


@pytest_asyncio.fixture
async def app_client(db_session: AsyncSession):
    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, db_session
    app.dependency_overrides.clear()


async def _as_super(c: AsyncClient, db: AsyncSession) -> None:
    await AuthService(db).create_user(email="su@clinic.uz", password="superpw", full_name="SU", role="super_admin")
    await db.commit()
    await _login(c, "su@clinic.uz", "superpw")


# --- helper ------------------------------------------------------------------
def test_short_name() -> None:
    assert short_name("Aliyev Akmal") == "Aliyev A."
    assert short_name("Aliyev") == "Aliyev"
    assert short_name("") is None and short_name(None) is None


# --- access ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_schedule_operator_forbidden(app_client) -> None:
    c, db = app_client
    await AuthService(db).create_user(email="op2@clinic.uz", password="operatorpw", full_name="Op", role="operator")
    await db.commit()
    await _login(c, "op2@clinic.uz", "operatorpw")
    assert (await c.get(f"{API}/manager/schedule")).status_code == 403


@pytest.mark.asyncio
async def test_schedule_unauth(app_client) -> None:
    c, _ = app_client
    assert (await c.get(f"{API}/manager/schedule")).status_code in (401, 403)


# --- seed + schedule + masking ----------------------------------------------
@pytest.mark.asyncio
async def test_seed_then_schedule_masked(app_client) -> None:
    c, db = app_client
    await _as_super(c, db)
    seeded = (await c.post(f"{API}/manager/seed-demo")).json()
    assert seeded["seeded"] is True and seeded["appointments"] == 5
    # idempotent
    assert (await c.post(f"{API}/manager/seed-demo")).json()["seeded"] is False

    appts = (await c.get(f"{API}/manager/schedule")).json()
    assert len(appts) == 5
    first = appts[0]
    assert first["patient_short"] == "Aliyev A."  # name shortened
    assert first["phone_masked"] and "+998901112233" not in str(first)  # phone masked
    assert "patient_phone" not in first and "patient_name" not in first  # raw never exposed
    assert first["doctor_name"] == "Karimov Bobur"


@pytest.mark.asyncio
async def test_doctor_workload(app_client) -> None:
    c, db = app_client
    await _as_super(c, db)
    await c.post(f"{API}/manager/seed-demo")
    docs = (await c.get(f"{API}/manager/doctors")).json()
    # Karimov has 3 of today's appointments, Rustamov 2.
    by_name = {d["full_name"]: d["appointments"] for d in docs}
    assert by_name["Karimov Bobur"] == 3 and by_name["Rustamov Sardor"] == 2


@pytest.mark.asyncio
async def test_reports_today(app_client) -> None:
    c, db = app_client
    await _as_super(c, db)
    await c.post(f"{API}/manager/seed-demo")
    rep = (await c.get(f"{API}/manager/reports?range=today")).json()
    assert rep["range"] == "today" and rep["total"] == 5
    assert rep["cancelled"] == 1 and rep["ai_created"] == 3
    assert rep["by_status"].get("confirmed") == 2


# --- validation --------------------------------------------------------------
@pytest.mark.asyncio
async def test_invalid_appointment_status_400(app_client) -> None:
    c, db = app_client
    await _as_super(c, db)
    r = await c.post(f"{API}/manager/appointments", json={"service": "x", "status": "bogus"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_create_doctor_and_appointment(app_client) -> None:
    c, db = app_client
    await _as_super(c, db)
    doc = (await c.post(f"{API}/manager/doctors", json={"full_name": "Test Doc", "specialty": "urolog"})).json()
    appt = (await c.post(f"{API}/manager/appointments", json={
        "service": "Konsultatsiya", "doctor_id": doc["id"], "patient_name": "Petrov Pavel",
        "patient_phone": "+998901119999", "status": "pending", "source": "manual",
    })).json()
    assert appt["doctor_name"] == "Test Doc" and appt["patient_short"] == "Petrov P."
    upd = (await c.patch(f"{API}/manager/appointments/{appt['id']}/status", json={"status": "confirmed"})).json()
    assert upd["status"] == "confirmed"
