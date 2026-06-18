"""CallbackTaskService — lifecycle for operator-busy callbacks (TZ §4.6).

Status machine:
  callback_required -> assigned   (assign)
  callback_required -> cancelled  (cancel; managers only at the API layer)
  assigned          -> completed  (complete)
  assigned          -> cancelled  (cancel)
  completed / cancelled           (terminal; not modifiable here)

Operator ownership rules are enforced here regardless of caller; the API layer
adds role guards (operator cannot cancel/reschedule).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.models.callback_task import CallbackTask

STATUS_REQUIRED = "callback_required"
STATUS_ASSIGNED = "assigned"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"
_TERMINAL = {STATUS_COMPLETED, STATUS_CANCELLED}


class CallbackError(Exception):
    """Base error (-> HTTP 400)."""


class CallbackNotFoundError(CallbackError):
    """-> HTTP 404."""


class CallbackPermissionError(CallbackError):
    """-> HTTP 403."""


class CallbackStateError(CallbackError):
    """Invalid transition / terminal task (-> HTTP 400)."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


class CallbackTaskService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _require(self, task_id: int) -> CallbackTask:
        task = await self._session.get(CallbackTask, task_id)
        if task is None:
            raise CallbackNotFoundError(f"callback {task_id} not found")
        return task

    async def list(
        self,
        *,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        reason: Optional[str] = None,
        assigned_to_me: bool = False,
        current_user_id: Optional[int] = None,
        limit: int = 200,
    ) -> list[CallbackTask]:
        stmt = select(CallbackTask)
        if status:
            stmt = stmt.where(CallbackTask.status == status)
        if priority:
            stmt = stmt.where(CallbackTask.priority == priority)
        if reason:
            stmt = stmt.where(CallbackTask.reason == reason)
        if assigned_to_me and current_user_id is not None:
            stmt = stmt.where(CallbackTask.assigned_to_user_id == current_user_id)
        stmt = stmt.order_by(CallbackTask.created_at.desc(), CallbackTask.id.desc()).limit(limit)
        return list((await self._session.execute(stmt)).scalars())

    async def assign(self, task_id: int, actor: AdminUser) -> CallbackTask:
        task = await self._require(task_id)
        if task.status in _TERMINAL:
            raise CallbackStateError("callback is in a terminal state")
        if actor.role == "operator" and task.assigned_to_user_id not in (None, actor.id):
            raise CallbackPermissionError("callback already assigned to another operator")
        task.assigned_to_user_id = actor.id
        task.status = STATUS_ASSIGNED
        task.last_status_changed_at = _now()
        await self._session.flush()
        return task

    async def complete(self, task_id: int, actor: AdminUser) -> CallbackTask:
        task = await self._require(task_id)
        if task.status in _TERMINAL:
            raise CallbackStateError("callback is in a terminal state")
        if task.status != STATUS_ASSIGNED:
            raise CallbackStateError("only an assigned callback can be completed")
        if actor.role == "operator" and task.assigned_to_user_id != actor.id:
            raise CallbackPermissionError("cannot complete a callback assigned to someone else")
        task.status = STATUS_COMPLETED
        task.completed_at = _now()
        task.last_status_changed_at = _now()
        await self._session.flush()
        return task

    async def cancel(self, task_id: int, actor: AdminUser) -> CallbackTask:
        task = await self._require(task_id)
        if task.status in _TERMINAL:
            raise CallbackStateError("callback is in a terminal state")
        task.status = STATUS_CANCELLED
        task.cancelled_at = _now()
        task.last_status_changed_at = _now()
        await self._session.flush()
        return task

    async def reschedule(self, task_id: int, due_at: datetime) -> CallbackTask:
        task = await self._require(task_id)
        if task.status in _TERMINAL:
            raise CallbackStateError("callback is in a terminal state")
        task.due_at = due_at
        task.rescheduled_at = _now()
        await self._session.flush()
        return task

    async def update_notes(self, task_id: int, actor: AdminUser, resolution_notes: str) -> CallbackTask:
        task = await self._require(task_id)
        if task.status in _TERMINAL:
            raise CallbackStateError("callback is in a terminal state")
        if actor.role == "operator" and task.assigned_to_user_id != actor.id:
            raise CallbackPermissionError("cannot edit notes on a callback assigned to someone else")
        task.resolution_notes = resolution_notes
        await self._session.flush()
        return task
