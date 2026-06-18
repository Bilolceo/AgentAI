# Audio storage + recording metadata

This adds the storage ABSTRACTION and database METADATA so future real voice
calls can keep audio safely. It is NOT real telephony and NOT real STT/TTS: the
voice pipeline still runs on mock providers. Audio blobs are kept OUT of the
database; Postgres stores only metadata.

## Components
- `AudioStorageProvider` (interface): `save_audio() -> StoredAudio`,
  `get_signed_url(storage_key)`, `delete_audio(storage_key)`.
- `StoredAudio`: storage_key, content_type, size_bytes, checksum_sha256,
  provider, url (nullable), duration_ms (nullable), metadata (safe dict).
- `InMemoryAudioStorage` (default, tests/dev): bytes in a process dict; nothing
  persisted; signed URL is a `memory://` placeholder.
- `LocalAudioStorage` (dev): writes bytes under `AUDIO_STORAGE_PATH`; signed URL
  is a `file://` placeholder.
- `AudioRecording` model/table: per-recording metadata (no blob). Fields:
  call_session_id, call_message_id, direction (inbound|outbound), kind
  (user_audio|ai_tts|full_call|system), storage_provider, storage_key,
  content_type, size_bytes, duration_ms, checksum_sha256, transcript_text,
  transcript_language, transcript_confidence, tts_voice, tts_text, is_deleted,
  expires_at, created_at, updated_at. Migration `0009_audio_recordings`.
- `AudioRecordingService`: create / list_for_call / list (filtered+paginated) /
  get / soft_delete.

## Pipeline integration
`VoicePipelineService` now (when a storage provider + recording service are
wired) saves:
- inbound caller audio -> `AudioRecording(direction=inbound, kind=user_audio)`
  with STT transcript metadata (text/language/confidence). Only when real audio
  bytes are present; the `text_override` path has no inbound audio so it is
  skipped.
- outbound TTS audio -> `AudioRecording(direction=outbound, kind=ai_tts)` with
  voice + text.
A storage failure maps to the same safe degraded response as an STT/TTS failure
(operator transfer; `degraded_stage="storage"`). The text safety pipeline is
unchanged. The API never returns raw audio bytes -- only metadata + recording ids.

## Config (.env)
- `AUDIO_STORAGE_PROVIDER=memory` (memory|local; s3_placeholder fails fast)
- `AUDIO_STORAGE_PATH=./data/audio` (local provider)
- `AUDIO_RETENTION_DAYS=90` (sets `expires_at`; no purge worker yet)
- `SIGNED_URL_TTL_SECONDS=300` (placeholder signed URLs)

## Admin endpoints (super_admin/admin only)
- `GET /api/v1/admin/audio-recordings` - list metadata. Safe filters:
  `call_id`, `direction` (inbound|outbound), `kind`
  (user_audio|ai_tts|full_call|system), `include_deleted` (soft-deleted hidden
  unless true), `limit` (1-200, default 50), `offset`. Newest first. No raw audio.
- `GET /api/v1/admin/audio-recordings/{id}` - one recording + a placeholder
  `signed_url` (may be null for ephemeral memory storage).
- `POST /api/v1/admin/audio-recordings/{id}/delete` - soft delete (audited).
Operators get 403; unauthenticated gets 401.

## Admin UI
`/admin/audio-recordings` (nav link shown to super_admin/admin only):
- Filter by call_id, direction, kind, and an "include deleted" toggle;
  prev/next pagination (page size 25).
- Table columns: id, call, direction, kind, content_type, size_bytes,
  duration_ms, transcript_language, transcript_confidence, tts_voice, expires_at,
  created_at, deleted. A `Delete` button (hidden for already-deleted rows) runs a
  confirmed soft-delete and refreshes the list.
- Detail view `/admin/audio-recordings/[id]`: full safe metadata (storage_key and
  checksum shortened), transcript_text, tts_text, expires/created/updated. If a
  `signed_url` exists it renders a link + audio player; otherwise it shows
  "No playable audio URL available." Raw audio bytes are never exposed in the UI.
- Operators visiting the page see a forbidden message (and the backend returns 403).

## Retention
`expires_at` is set from `AUDIO_RETENTION_DAYS` at save time. No purge worker is
implemented yet; a future Celery beat job will delete blobs + soft-delete rows
past `expires_at`.

## Future real object storage (not implemented)
S3 / Cloudflare R2 behind `AudioStorageProvider`: `save_audio` uploads and
returns a real signed URL from `get_signed_url`; `delete_audio` removes the
object. Selection stays via `AUDIO_STORAGE_PROVIDER`. Secrets come from env
(`.env.example` placeholders) and are never stored in `metadata` or returned by
the API.

## Scope note
This task is metadata + storage abstraction only. No SIP/Twilio, no real
STT/TTS, no real upload, no audio purge worker. See docs/voice-layer.md for the
voice pipeline and next steps toward a real voice pilot.
