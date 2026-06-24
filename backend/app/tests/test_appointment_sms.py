"""Appointment SMS confirmation (mock channel by default)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app
from app.models.doctor import Doctor
from app.models.notification_log import NotificationLog
from app.services.auth.service import AuthService
from app.services.notifications.messages import appointment_sms_text

API = "/api/v1"


@pytest_asyncio.fixture
async def app_client(db_session: AsyncSession):
    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, db_session
    app.dependency_overrides.clear()


async def _login(c: AsyncClient, db: AsyncSession) -> None:
    await AuthService(db).create_user(email="m@clinic.uz", password="managerpw", full_name="Mgr", role="manager")
    await db.commit()
    r = await c.post(f"{API}/auth/login", json={"email": "m@clinic.uz", "password": "managerpw"})
    c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"


def _next_weekday() -> str:
    d = datetime.now(timezone.utc) + timedelta(days=2)
    while d.weekday() == 6:
        d += timedelta(days=1)
    return d.strftime("%Y-%m-%d")


# --- message composition -----------------------------------------------------
def test_message_text_uz_ru() -> None:
    when = datetime(2026, 6, 25, 10, 0)
    uz = appointment_sms_text(kind="confirmed", patient_name="Aliyev Akmal", scheduled_at=when, doctor_name="Dr X")
    assert "TASDIQLANDI" in uz and "25.06.2026 10:00" in uz and "Dr X" in uz
    ru = appointment_sms_text(kind="cancelled", patient_name="Ivan", scheduled_at=when, locale="ru")
    assert "отмен" in ru.lower() and "25.06.2026 10:00" in ru
    received = appointment_sms_text(kind="booking_received", patient_name="", scheduled_at=when)
    assert "qabul qilindi" in received


# --- web booking logs a received SMS -----------------------------------------
@pytest.mark.asyncio
async def test_public_booking_logs_sms(app_client) -> None:
    c, db = app_client
    doc = Doctor(full_name="Karimov Bobur", specialty="urolog", working_hours="09:00-18:00",
                 working_days="mon,tue,wed,thu,fri,sat", is_active=True)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    r = await c.post(f"{API}/public/appointments", json={
        "doctor_id": doc.id, "date": _next_weekday(), "time": "10:00",
        "patient_name": "Valiyev Olim", "patient_phone": "+998901112233",
    })
    assert r.status_code == 200
    rows = (await db.execute(select(NotificationLog).where(NotificationLog.kind == "booking_received"))).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == "mock" and rows[0].to_phone == "+998901112233"
    assert "qabul qilindi" in rows[0].body


# --- manager confirm logs a confirmed SMS; cancel logs cancelled -------------
@pytest.mark.asyncio
async def test_confirm_and_cancel_log_sms(app_client) -> None:
    c, db = app_client
    await _login(c, db)
    doc = (await c.post(f"{API}/manager/doctors", json={"full_name": "Test Doc", "specialty": "urolog"})).json()
    appt = (await c.post(f"{API}/manager/appointments", json={
        "service": "Konsultatsiya", "doctor_id": doc["id"], "patient_name": "Petrov Pavel",
        "patient_phone": "+998901119999", "status": "pending", "source": "web",
    })).json()

    await c.patch(f"{API}/manager/appointments/{appt['id']}/status", json={"status": "confirmed"})
    await c.patch(f"{API}/manager/appointments/{appt['id']}/status", json={"status": "cancelled"})

    kinds = (await db.execute(select(NotificationLog.kind).where(NotificationLog.appointment_id == appt["id"]))).scalars().all()
    assert "confirmed" in kinds and "cancelled" in kinds


# --- a status with no patient notification writes nothing --------------------
@pytest.mark.asyncio
async def test_arrived_status_no_sms(app_client) -> None:
    c, db = app_client
    await _login(c, db)
    doc = (await c.post(f"{API}/manager/doctors", json={"full_name": "Doc2"})).json()
    appt = (await c.post(f"{API}/manager/appointments", json={
        "service": "Konsultatsiya", "doctor_id": doc["id"], "patient_phone": "+998901110000",
        "status": "confirmed", "source": "manual",
    })).json()
    # drain the confirmed-create? create uses status confirmed but no notify on create.
    await c.patch(f"{API}/manager/appointments/{appt['id']}/status", json={"status": "arrived"})
    total = (await db.execute(
        select(func.count()).select_from(NotificationLog).where(NotificationLog.appointment_id == appt["id"])
    )).scalar_one()
    assert total == 0
