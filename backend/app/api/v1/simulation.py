"""Text-based call simulation — the MVP entry point (no telephony).

Routes are thin: all logic is in CallSessionService.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import build_call_session_service, get_session
from app.schemas.simulation import (
    MessageRequest,
    MessageResponse,
    StartCallRequest,
    StartCallResponse,
)

router = APIRouter()


@router.post("/calls", response_model=StartCallResponse, status_code=201)
async def start_call(
    payload: StartCallRequest, session: AsyncSession = Depends(get_session)
) -> StartCallResponse:
    svc = build_call_session_service(session)
    start = await svc.start_call(
        from_number=payload.from_number,
        to_number=payload.to_number,
        language_code=payload.language,
    )
    return StartCallResponse(
        call_id=start.call.id, greeting=start.greeting, language=start.language.value
    )


@router.post("/calls/{call_id}/message", response_model=MessageResponse)
async def send_message(
    call_id: int, payload: MessageRequest, session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    svc = build_call_session_service(session)
    try:
        outcome = await svc.handle_message(
            call_id=call_id, text=payload.text, language=payload.language
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MessageResponse(
        reply=outcome.reply,
        action=outcome.action,
        reason_code=outcome.reason_code,
        transferred=outcome.transferred,
        language=outcome.language,
        transfer_reason=outcome.transfer_reason,
        priority=outcome.priority,
        transfer_status=outcome.transfer_status,
        callback_required=outcome.callback_required,
        sources=outcome.sources,
    )


@router.post("/calls/{call_id}/end")
async def end_call(call_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    svc = build_call_session_service(session)
    try:
        call = await svc.end_call(call_id=call_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"call_id": call.id, "status": call.status}
