"""AdminDashboardService — read-only aggregation for the admin pages.

All admin read logic lives here; routes only call these methods.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.models.call import Call
from app.models.callback_task import CallbackTask
from app.models.knowledge_item import KnowledgeItem


def _duration_seconds(call: Call) -> Optional[int]:
    if call.ended_at and call.started_at:
        return int((call.ended_at - call.started_at).total_seconds())
    return None


def _call_dict(call: Call) -> dict:
    return {
        "id": call.id,
        "twilio_call_sid": call.twilio_call_sid,
        "from_number": call.from_number,
        "to_number": call.to_number,
        "language": call.language,
        "status": call.status,
        "started_at": call.started_at,
        "ended_at": call.ended_at,
        "duration_seconds": _duration_seconds(call),
    }


def _callback_dict(task: CallbackTask) -> dict:
    return {
        "id": task.id,
        "call_session_id": task.call_session_id,
        "patient_phone": task.patient_phone,
        "reason": task.reason,
        "priority": task.priority,
        "status": task.status,
        "due_at": task.due_at,
        "notes": task.notes,
        "created_at": task.created_at,
    }


class AdminDashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def stats(self) -> dict:
        total_calls = await self._count(select(func.count()).select_from(Call))
        transferred = await self._count(
            select(func.count()).select_from(Call).where(Call.status == "transferred")
        )
        operator_transfers = await self._count(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.event == "operator_transfer_requested")
        )
        callbacks_required = await self._count(
            select(func.count())
            .select_from(CallbackTask)
            .where(CallbackTask.status == "callback_required")
        )
        kb_items = await self._count(select(func.count()).select_from(KnowledgeItem))

        recent = (
            await self._session.execute(
                select(Call).order_by(Call.started_at.desc(), Call.id.desc()).limit(10)
            )
        ).scalars()

        return {
            "total_calls": total_calls,
            "ai_resolved": total_calls - transferred,
            "operator_transfers": operator_transfers,
            "callbacks_required": callbacks_required,
            "kb_items": kb_items,
            "recent_calls": [_call_dict(c) for c in recent],
        }

    async def list_calls(
        self, *, status: Optional[str] = None, language: Optional[str] = None, limit: int = 100
    ) -> list[dict]:
        stmt = select(Call)
        if status:
            stmt = stmt.where(Call.status == status)
        if language:
            stmt = stmt.where(Call.language == language)
        stmt = stmt.order_by(Call.started_at.desc(), Call.id.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars()
        return [_call_dict(c) for c in rows]

    async def call_detail(self, call_id: int) -> Optional[dict]:
        call = (
            await self._session.execute(
                select(Call).where(Call.id == call_id).options(selectinload(Call.transcripts))
            )
        ).scalar_one_or_none()
        if call is None:
            return None

        audits = list(
            (
                await self._session.execute(
                    select(AuditLog).where(AuditLog.call_id == call_id).order_by(AuditLog.id)
                )
            ).scalars()
        )

        transfer: Optional[dict] = None
        sources: list[dict] = []
        seen_source_ids: set = set()
        reason_codes: list[str] = []
        for a in audits:
            data = a.data or {}
            if a.event == "operator_transfer_requested":
                transfer = {
                    "reason": data.get("reason"),
                    "priority": data.get("priority"),
                    "status": data.get("status"),
                }
            elif a.event == "ai_response_generated":
                for src in data.get("sources") or []:
                    if src.get("id") not in seen_source_ids:
                        seen_source_ids.add(src.get("id"))
                        sources.append(src)
            elif a.event == "safety_guard_triggered":
                rc = data.get("reason_code")
                if rc:
                    reason_codes.append(rc)

        callback = (
            await self._session.execute(
                select(CallbackTask)
                .where(CallbackTask.call_session_id == call_id)
                .order_by(CallbackTask.id.desc())
            )
        ).scalars().first()

        detail = _call_dict(call)
        detail.update(
            {
                "transcripts": [
                    {"id": t.id, "role": t.role, "text": t.text, "created_at": t.created_at}
                    for t in sorted(call.transcripts, key=lambda t: t.id)
                ],
                "transfer": transfer,
                "callback": _callback_dict(callback) if callback else None,
                "sources": sources,
                "reason_codes": reason_codes,
                "audit_events": [
                    {"event": a.event, "data": a.data, "created_at": a.created_at} for a in audits
                ],
            }
        )
        return detail

    async def list_callbacks(
        self, *, status: Optional[str] = None, limit: int = 100
    ) -> list[dict]:
        stmt = select(CallbackTask)
        if status:
            stmt = stmt.where(CallbackTask.status == status)
        stmt = stmt.order_by(CallbackTask.created_at.desc(), CallbackTask.id.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars()
        return [_callback_dict(t) for t in rows]

    async def _count(self, stmt) -> int:
        return int((await self._session.execute(stmt)).scalar_one())
