"""Qo'ng'iroqlar va transkriptlar (admin)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_session
from app.core.security import require_api_key
from app.models.call import Call
from app.schemas.call import CallDetailOut, CallOut

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("", response_model=list[CallOut])
async def list_calls(
    session: AsyncSession = Depends(get_session), limit: int = 50
) -> list[Call]:
    rows = await session.execute(select(Call).order_by(Call.started_at.desc()).limit(limit))
    return list(rows.scalars().all())


@router.get("/{call_id}", response_model=CallDetailOut)
async def get_call(call_id: int, session: AsyncSession = Depends(get_session)) -> Call:
    stmt = select(Call).where(Call.id == call_id).options(selectinload(Call.transcripts))
    call = (await session.execute(stmt)).scalar_one_or_none()
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")
    return call
