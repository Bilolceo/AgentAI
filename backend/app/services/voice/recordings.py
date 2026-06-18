"""AudioRecordingService — persists audio metadata rows (no raw blobs)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audio_recording import AudioRecording
from app.services.voice.storage import StoredAudio


class AudioRecordingService:
    def __init__(self, session: AsyncSession, retention_days: int = 90) -> None:
        self._session = session
        self._retention_days = retention_days

    async def create(
        self,
        *,
        call_session_id: int,
        direction: str,
        kind: str,
        stored: StoredAudio,
        call_message_id: Optional[int] = None,
        transcript_text: Optional[str] = None,
        transcript_language: Optional[str] = None,
        transcript_confidence: Optional[float] = None,
        tts_voice: Optional[str] = None,
        tts_text: Optional[str] = None,
    ) -> AudioRecording:
        rec = AudioRecording(
            call_session_id=call_session_id,
            call_message_id=call_message_id,
            direction=direction,
            kind=kind,
            storage_provider=stored.provider,
            storage_key=stored.storage_key,
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
            duration_ms=stored.duration_ms,
            checksum_sha256=stored.checksum_sha256,
            transcript_text=transcript_text,
            transcript_language=transcript_language,
            transcript_confidence=transcript_confidence,
            tts_voice=tts_voice,
            tts_text=tts_text,
            expires_at=datetime.now(timezone.utc) + timedelta(days=self._retention_days),
        )
        self._session.add(rec)
        await self._session.flush()
        return rec

    async def list_for_call(
        self, call_session_id: int, *, include_deleted: bool = False
    ) -> list[AudioRecording]:
        stmt = select(AudioRecording).where(
            AudioRecording.call_session_id == call_session_id
        )
        if not include_deleted:
            stmt = stmt.where(AudioRecording.is_deleted.is_(False))
        stmt = stmt.order_by(AudioRecording.id)
        return list((await self._session.execute(stmt)).scalars().all())

    async def list(
        self,
        *,
        call_session_id: Optional[int] = None,
        direction: Optional[str] = None,
        kind: Optional[str] = None,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AudioRecording]:
        """Filtered, paginated listing for the admin UI. Soft-deleted rows are
        hidden unless include_deleted is set. Newest first."""
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        stmt = select(AudioRecording)
        if call_session_id is not None:
            stmt = stmt.where(AudioRecording.call_session_id == call_session_id)
        if direction:
            stmt = stmt.where(AudioRecording.direction == direction)
        if kind:
            stmt = stmt.where(AudioRecording.kind == kind)
        if not include_deleted:
            stmt = stmt.where(AudioRecording.is_deleted.is_(False))
        stmt = stmt.order_by(AudioRecording.id.desc()).limit(limit).offset(offset)
        return list((await self._session.execute(stmt)).scalars().all())

    async def get(self, recording_id: int, *, include_deleted: bool = True) -> Optional[AudioRecording]:
        stmt = select(AudioRecording).where(AudioRecording.id == recording_id)
        if not include_deleted:
            stmt = stmt.where(AudioRecording.is_deleted.is_(False))
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def soft_delete(self, recording_id: int) -> Optional[AudioRecording]:
        rec = await self.get(recording_id)
        if rec is None or rec.is_deleted:
            return rec
        rec.is_deleted = True
        await self._session.flush()
        return rec
