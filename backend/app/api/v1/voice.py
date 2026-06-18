"""Local voice simulation bridge — NOT real telephony.

Routes are thin: STT/AI/TTS orchestration lives in VoicePipelineService.
"""
from __future__ import annotations

import base64
import binascii

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import build_voice_pipeline_service, get_session
from app.core.config import settings
from app.schemas.voice import (
    AudioMeta,
    STTMeta,
    VoiceSimulateRequest,
    VoiceSimulateResponse,
)

router = APIRouter()


@router.post("/simulate", response_model=VoiceSimulateResponse)
async def voice_simulate(
    payload: VoiceSimulateRequest, session: AsyncSession = Depends(get_session)
) -> VoiceSimulateResponse:
    if not payload.text_override and not payload.audio_base64:
        raise HTTPException(status_code=422, detail="Provide text_override or audio_base64")

    content_type = payload.content_type or "application/octet-stream"
    if payload.content_type and payload.content_type not in settings.stt_allowed_content_types_list:
        raise HTTPException(
            status_code=422, detail=f"Unsupported content_type: {payload.content_type}"
        )

    audio = b""
    if payload.audio_base64:
        try:
            audio = base64.b64decode(payload.audio_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(status_code=422, detail="audio_base64 is not valid base64") from exc
        if len(audio) > settings.stt_max_audio_bytes:
            raise HTTPException(
                status_code=422,
                detail=f"Audio exceeds STT_MAX_AUDIO_BYTES ({settings.stt_max_audio_bytes})",
            )

    svc = build_voice_pipeline_service(session)
    try:
        outcome = await svc.process(
            call_id=payload.call_id,
            audio=audio,
            content_type=content_type,
            text_override=payload.text_override,
            from_number=payload.from_number,
            to_number=payload.to_number,
            language=payload.language,
        )
    except ValueError as exc:  # call not found
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    stt_meta = None
    if outcome.stt is not None:
        stt_meta = STTMeta(
            language=outcome.stt.language,
            confidence=outcome.stt.confidence,
            duration_ms=outcome.stt.duration_ms,
            provider=outcome.stt.provider_metadata.get("provider"),
        )
    audio_meta = None
    if outcome.audio is not None:
        audio_meta = AudioMeta(
            voice=outcome.audio.voice,
            language=outcome.audio.language,
            content_type=outcome.audio.content_type,
            duration_ms=outcome.audio.duration_ms,
            audio_bytes_len=len(outcome.audio.audio_bytes or b""),
            audio_url=outcome.audio.audio_url,
            provider=outcome.audio.provider_metadata.get("provider"),
        )

    return VoiceSimulateResponse(
        call_id=outcome.call_id,
        transcript=outcome.transcript,
        ai_text=outcome.ai_text,
        action=outcome.action,
        reason_code=outcome.reason_code,
        transferred=outcome.transferred,
        language=outcome.language,
        transfer_reason=outcome.transfer_reason,
        priority=outcome.priority,
        transfer_status=outcome.transfer_status,
        callback_required=outcome.callback_required,
        sources=outcome.sources,
        degraded_stage=outcome.degraded_stage,
        stt=stt_meta,
        audio=audio_meta,
        inbound_recording_id=outcome.inbound_recording_id,
        outbound_recording_id=outcome.outbound_recording_id,
    )
