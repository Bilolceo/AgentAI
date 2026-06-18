"""TelephonyStreamService — Twilio Media Streams lifecycle (WebSocket spike).

Tracks a media stream and counts frames/bytes. It NEVER stores or logs the raw
audio payload. This is a parser/lifecycle spike: no streaming STT/TTS, no
barge-in. Base64 media is decoded only to measure size and validate.
"""
from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telephony_call import TelephonyCall
from app.models.telephony_stream import TelephonyStream

# Keys from the start event's mediaFormat we keep (safe, non-sensitive).
_MEDIA_FORMAT_KEYS = ("encoding", "sampleRate", "channels")


class TelephonyStreamError(Exception):
    """Malformed stream event; the WebSocket handler closes safely."""


def _int_or_none(v) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


class TelephonyStreamService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        max_frame_bytes: int = 8000,
        max_frames_per_call: int = 50_000,
    ) -> None:
        self._session = session
        self._max_frame_bytes = max_frame_bytes
        self._max_frames_per_call = max_frames_per_call

    async def start_stream(self, event: dict) -> TelephonyStream:
        start = event.get("start") or {}
        if not isinstance(start, dict):
            raise TelephonyStreamError("invalid start event")
        stream_sid = event.get("streamSid") or start.get("streamSid")
        call_sid = start.get("callSid")

        telephony_call_id = None
        if call_sid:
            tel = await self._find_call(call_sid)
            if tel is not None:
                telephony_call_id = tel.id

        metadata = self._safe_start_metadata(start)
        stream = TelephonyStream(
            provider="twilio",
            provider_call_id=call_sid,
            stream_sid=stream_sid,
            telephony_call_id=telephony_call_id,
            status="active",
            media_frames_count=0,
            media_bytes_count=0,
            stream_metadata=metadata or None,
            started_at=datetime.now(timezone.utc),
        )
        self._session.add(stream)
        await self._session.commit()
        await self._session.refresh(stream)
        return stream

    async def record_media_frame(self, stream: TelephonyStream, event: dict) -> int:
        """Count one media frame. Returns the decoded byte count (0 if invalid).

        Enforces per-call frame cap; never buffers/persists the raw payload.
        """
        if stream.media_frames_count >= self._max_frames_per_call:
            return 0
        media = event.get("media") or {}
        payload = media.get("payload") if isinstance(media, dict) else None
        n_bytes = 0
        if isinstance(payload, str) and payload:
            try:
                decoded = base64.b64decode(payload, validate=True)
                n_bytes = min(len(decoded), self._max_frame_bytes)
            except (binascii.Error, ValueError):
                n_bytes = 0  # invalid base64 -> count the frame, zero bytes

        stream.media_frames_count += 1
        stream.media_bytes_count += n_bytes
        seq = _int_or_none(event.get("sequenceNumber"))
        if seq is not None:
            stream.last_sequence_number = seq
        # Persist periodically so a dropped socket still leaves a recent count.
        if stream.media_frames_count % 50 == 0:
            await self._session.commit()
        return n_bytes

    async def stop_stream(self, stream: TelephonyStream) -> TelephonyStream:
        if stream.status != "stopped":
            stream.status = "stopped"
            stream.stopped_at = datetime.now(timezone.utc)
            await self._session.commit()
            await self._session.refresh(stream)
        return stream

    # --- admin reads --------------------------------------------------------
    async def list(
        self,
        *,
        call_sid: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TelephonyStream]:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        stmt = select(TelephonyStream)
        if call_sid:
            stmt = stmt.where(TelephonyStream.provider_call_id == call_sid)
        if status:
            stmt = stmt.where(TelephonyStream.status == status)
        stmt = stmt.order_by(TelephonyStream.id.desc()).limit(limit).offset(offset)
        return list((await self._session.execute(stmt)).scalars().all())

    async def get(self, stream_id: int) -> Optional[TelephonyStream]:
        stmt = select(TelephonyStream).where(TelephonyStream.id == stream_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    # --- helpers ------------------------------------------------------------
    async def _find_call(self, sid: str) -> Optional[TelephonyCall]:
        stmt = (
            select(TelephonyCall)
            .where(TelephonyCall.provider_call_id == sid)
            .order_by(TelephonyCall.id.desc())
        )
        return (await self._session.execute(stmt)).scalars().first()

    @staticmethod
    def _safe_start_metadata(start: dict) -> dict:
        meta: dict = {}
        tracks = start.get("tracks")
        if isinstance(tracks, list):
            meta["tracks"] = [str(t) for t in tracks]
        media_format = start.get("mediaFormat")
        if isinstance(media_format, dict):
            meta["media_format"] = {
                k: media_format[k] for k in _MEDIA_FORMAT_KEYS if k in media_format
            }
        return meta
