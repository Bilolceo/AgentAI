"""KB management: RBAC on mutations, audit events, inactive excluded from search."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.main import app
from app.models.audit_log import AuditLog
from app.services.auth.service import AuthService
from app.services.knowledge.intent import KBIntent
from app.services.knowledge.service import KBCategory, KnowledgeBaseService

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


def _item_body(**over) -> dict:
    base = {
        "category": KBCategory.FAQ.value,
        "title": "Test item",
        "content_uz": "Test uz",
        "content_ru": "Test ru",
        "tags": ["x"],
        "is_active": True,
    }
    base.update(over)
    return base


# === RBAC ====================================================================
@pytest.mark.asyncio
async def test_admin_can_create_update_deactivate(client, db_session) -> None:
    token = await _token(client, db_session, "admin@clinic.uz", "admin")

    created = await client.post(f"{API}/admin/knowledge-items", headers=_b(token), json=_item_body())
    assert created.status_code == 201
    item_id = created.json()["id"]

    updated = await client.patch(
        f"{API}/admin/knowledge-items/{item_id}", headers=_b(token), json={"title": "New title"}
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "New title"

    deact = await client.post(f"{API}/admin/knowledge-items/{item_id}/deactivate", headers=_b(token))
    assert deact.status_code == 200
    assert deact.json()["is_active"] is False

    act = await client.post(f"{API}/admin/knowledge-items/{item_id}/activate", headers=_b(token))
    assert act.json()["is_active"] is True


@pytest.mark.asyncio
async def test_operator_cannot_mutate_kb(client, db_session) -> None:
    op = await _token(client, db_session, "op@clinic.uz", "operator")
    # seed one item directly so an id exists
    kb = KnowledgeBaseService(db_session)
    item = await kb.create(category=KBCategory.FAQ.value, title="T", content_uz="u", content_ru="r", tags=[])
    await db_session.commit()

    assert (await client.post(f"{API}/admin/knowledge-items", headers=_b(op), json=_item_body())).status_code == 403
    assert (await client.patch(f"{API}/admin/knowledge-items/{item.id}", headers=_b(op), json={"title": "x"})).status_code == 403
    assert (await client.post(f"{API}/admin/knowledge-items/{item.id}/deactivate", headers=_b(op))).status_code == 403
    assert (await client.delete(f"{API}/admin/knowledge-items/{item.id}", headers=_b(op))).status_code == 403


@pytest.mark.asyncio
async def test_operator_cannot_list_kb(client, db_session) -> None:
    op = await _token(client, db_session, "op2@clinic.uz", "operator")
    assert (await client.get(f"{API}/admin/knowledge-items", headers=_b(op))).status_code == 403


# === Audit ===================================================================
@pytest.mark.asyncio
async def test_mutation_audit_events(client, db_session) -> None:
    token = await _token(client, db_session, "admin@clinic.uz", "admin")
    item_id = (await client.post(f"{API}/admin/knowledge-items", headers=_b(token), json=_item_body())).json()["id"]
    await client.patch(f"{API}/admin/knowledge-items/{item_id}", headers=_b(token), json={"title": "Y"})
    await client.post(f"{API}/admin/knowledge-items/{item_id}/deactivate", headers=_b(token))
    await client.delete(f"{API}/admin/knowledge-items/{item_id}", headers=_b(token))

    events = set((await db_session.execute(select(AuditLog.event))).scalars().all())
    assert "knowledge_item_created" in events
    assert "knowledge_item_updated" in events
    assert "knowledge_item_deactivated" in events
    assert "knowledge_item_deleted" in events


# === Inactive excluded from AI search =======================================
@pytest.mark.asyncio
async def test_inactive_item_not_used_by_search(client, db_session) -> None:
    token = await _token(client, db_session, "admin@clinic.uz", "admin")
    body = _item_body(
        category=KBCategory.SERVICES_PRICES.value,
        title="Uniq service",
        content_uz="uniqtok123 narxi: 10 000 so'm",
        content_ru="uniqtok123 cena",
        tags=["uniqtok123", "narx"],
    )
    item_id = (await client.post(f"{API}/admin/knowledge-items", headers=_b(token), json=body)).json()["id"]

    kb = KnowledgeBaseService(db_session)
    found = await kb.search("uniqtok123 narxi", "uz-UZ", intent=KBIntent.PRICE)
    assert any(m.id == item_id for m in found)

    await client.post(f"{API}/admin/knowledge-items/{item_id}/deactivate", headers=_b(token))
    after = await kb.search("uniqtok123 narxi", "uz-UZ", intent=KBIntent.PRICE)
    assert all(m.id != item_id for m in after)
