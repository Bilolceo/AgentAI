"""Public self-service booking (customer-facing, no auth)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app
from app.models.doctor import Doctor
from app.services.clinic.booking import (
    BookingError,
    normalize_phone,
    validate_name,
)

API = "/api/v1"


@pytest_asyncio.fixture
async def app_client(db_session: AsyncSession):
    from app.api.v1 import public_booking

    public_booking._hits.clear()  # reset the in-memory rate limiter between tests

    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, db_session
    app.dependency_overrides.clear()


async def _make_doctor(db: AsyncSession, **kw) -> Doctor:
    doc = Doctor(full_name=kw.get("full_name", "Aliyev Akmal"), specialty=kw.get("specialty", "urolog"),
                 working_hours=kw.get("working_hours", "09:00-18:00"),
                 working_days=kw.get("working_days", "mon,tue,wed,thu,fri,sat"), is_active=kw.get("is_active", True))
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


def _next_weekday() -> str:
    """A date a few days ahead that is Mon..Sat (never Sunday)."""
    d = datetime.now(timezone.utc) + timedelta(days=2)
    while d.weekday() == 6:  # Sunday
        d += timedelta(days=1)
    return d.strftime("%Y-%m-%d")


# --- pure validation ---------------------------------------------------------
def test_normalize_phone() -> None:
    assert normalize_phone("+998901234567") == "+998901234567"
    assert normalize_phone("998 90 123 45 67") == "+998901234567"
    with pytest.raises(BookingError):
        normalize_phone("12345")


def test_validate_name() -> None:
    assert validate_name("  Ali Valiyev ") == "Ali Valiyev"
    with pytest.raises(BookingError):
        validate_name("x")


# --- public read endpoints (no auth) -----------------------------------------
@pytest.mark.asyncio
async def test_services_and_doctors_public(app_client) -> None:
    c, db = app_client
    await _make_doctor(db, full_name="Aliyev Akmal", specialty="urolog")
    services = (await c.get(f"{API}/public/services")).json()
    assert any(s["specialty"] == "urolog" and s["doctor_count"] >= 1 for s in services)
    docs = (await c.get(f"{API}/public/doctors", params={"specialty": "urolog"})).json()
    assert docs and docs[0]["full_name"] == "Aliyev Akmal"
    # public doctor view must not leak working schedule internals
    assert "working_hours" not in docs[0] and "is_active" not in docs[0]


@pytest.mark.asyncio
async def test_slots_returns_free_times(app_client) -> None:
    c, db = app_client
    doc = await _make_doctor(db)
    date = _next_weekday()
    body = (await c.get(f"{API}/public/slots", params={"doctor_id": doc.id, "date": date})).json()
    assert body["doctor_id"] == doc.id
    assert "09:00" in body["slots"] and "13:00" not in body["slots"]  # lunch skipped


# --- booking happy path + conflicts ------------------------------------------
@pytest.mark.asyncio
async def test_book_creates_pending(app_client) -> None:
    c, db = app_client
    doc = await _make_doctor(db)
    date = _next_weekday()
    r = await c.post(f"{API}/public/appointments", json={
        "doctor_id": doc.id, "date": date, "time": "10:00",
        "patient_name": "Valiyev Olim", "patient_phone": "+998901112233",
    })
    assert r.status_code == 200
    out = r.json()
    assert out["ok"] and out["status"] == "pending" and out["reference"].startswith("BR-")


@pytest.mark.asyncio
async def test_double_book_same_slot_rejected(app_client) -> None:
    c, db = app_client
    doc = await _make_doctor(db)
    date = _next_weekday()
    payload = {"doctor_id": doc.id, "date": date, "time": "11:00",
               "patient_name": "Birinchi Mijoz", "patient_phone": "+998901112200"}
    assert (await c.post(f"{API}/public/appointments", json=payload)).status_code == 200
    # The slot is now gone from availability...
    slots = (await c.get(f"{API}/public/slots", params={"doctor_id": doc.id, "date": date})).json()["slots"]
    assert "11:00" not in slots
    # ...and a second booking on it is rejected.
    payload2 = {**payload, "patient_name": "Ikkinchi Mijoz", "patient_phone": "+998901112201"}
    r = await c.post(f"{API}/public/appointments", json=payload2)
    assert r.status_code == 400 and r.json()["detail"] == "slot_taken"


@pytest.mark.asyncio
async def test_book_bad_phone_rejected(app_client) -> None:
    c, db = app_client
    doc = await _make_doctor(db)
    r = await c.post(f"{API}/public/appointments", json={
        "doctor_id": doc.id, "date": _next_weekday(), "time": "12:00",
        "patient_name": "Test Mijoz", "patient_phone": "000",
    })
    assert r.status_code == 400 and r.json()["detail"] == "invalid_phone"


@pytest.mark.asyncio
async def test_book_past_date_no_slots(app_client) -> None:
    c, db = app_client
    doc = await _make_doctor(db)
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    slots = (await c.get(f"{API}/public/slots", params={"doctor_id": doc.id, "date": yesterday})).json()["slots"]
    assert slots == []


@pytest.mark.asyncio
async def test_public_callback_creates_lead(app_client) -> None:
    c, db = app_client
    r = await c.post(f"{API}/public/callback", json={
        "name": "Olim Valiyev", "phone": "+998901112233", "message": "Qayta qo'ng'iroq qiling",
    })
    assert r.status_code == 200 and r.json()["ok"]
    # surfaces to staff via /manager/leads (needs manager auth)
    from app.services.auth.service import AuthService
    await AuthService(db).create_user(email="mgr@clinic.uz", password="managerpw", full_name="M", role="manager")
    await db.commit()
    tok = (await c.post(f"{API}/auth/login", json={"email": "mgr@clinic.uz", "password": "managerpw"})).json()["access_token"]
    leads = (await c.get(f"{API}/manager/leads", headers={"Authorization": f"Bearer {tok}"})).json()
    assert len(leads) == 1 and leads[0]["service"] == "Onlayn so'rov"


@pytest.mark.asyncio
async def test_public_callback_bad_phone(app_client) -> None:
    c, _ = app_client
    r = await c.post(f"{API}/public/callback", json={"name": "Olim", "phone": "123"})
    assert r.status_code == 400 and r.json()["detail"] == "invalid_phone"
