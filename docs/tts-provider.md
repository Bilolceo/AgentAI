# TTS provider (mock + real OpenAI TTS)

The voice pipeline depends only on `TTSProvider`. The provider is selected by
`TTS_PROVIDER`. Mock is the default and is the only one used by tests and CI.

## Mock mode (default, no key, deterministic)
`TTS_PROVIDER=mock` (default). `MockTTSProvider` returns deterministic fake audio
(`b"MOCK-AUDIO:" + text`), `content_type=audio/mpeg`, and resolves the voice from
`DEFAULT_VOICE_UZ` / `DEFAULT_VOICE_RU` by language. No external calls, no key.

    cd backend
    # local voice simulate (mock STT + mock TTS):
    curl -s -X POST http://localhost:8000/api/v1/voice/simulate \
      -H 'Content-Type: application/json' \
      -d '{"text_override":"Klinika manzili qayerda?"}'

## Real TTS (OpenAI) - opt-in
`TTS_PROVIDER=openai_tts`. `RealTTSProvider` lazy-imports the OpenAI SDK and calls
`audio.speech.create` (`response_format` = the configured audio format). It returns
the synthesized `audio_bytes`, the resolved `voice`, and the `content_type` for the
configured format. OpenAI TTS returns no duration, so `duration_ms=None`. The
adapter:
- wraps the call in a timeout -> `TTSProviderTimeoutError`,
- rejects text longer than `TTS_MAX_TEXT_CHARS` -> `TTSProviderError`,
- sanitizes any failure to a type name -> `TTSProviderError` (no payload/secret),
- never logs raw audio or the API key.
Any failure maps to the safe degraded path (operator transfer; transcript and AI
text are still returned, audio metadata is degraded).

### Voice selection (deterministic)
- explicit `voice` override > language locale.
- Uzbek -> `TTS_VOICE_UZ` (or `DEFAULT_VOICE_UZ` if empty).
- Russian -> `TTS_VOICE_RU` (or `DEFAULT_VOICE_RU` if empty).

### Env vars
- `TTS_PROVIDER=openai_tts`
- `OPENAI_API_KEY=sk-...`  (reused; missing key fails fast at startup)
- `TTS_MODEL=tts-1`
- `TTS_VOICE_UZ=alloy`  (OpenAI voice name; empty -> DEFAULT_VOICE_UZ)
- `TTS_VOICE_RU=nova`   (OpenAI voice name; empty -> DEFAULT_VOICE_RU)
- `TTS_AUDIO_FORMAT=mp3`  (mp3|wav|opus|aac|flac|pcm; unsupported -> fail fast)
- `TTS_TIMEOUT_SECONDS=15`
- `TTS_MAX_TEXT_CHARS=4000`  (over this -> safe operator transfer)

### Install + run (real)
    cd backend
    pip install -e ".[tts]"          # installs the OpenAI SDK (not in default deps)
    export TTS_PROVIDER=openai_tts
    export OPENAI_API_KEY=sk-...
    curl -s -X POST http://localhost:8000/api/v1/voice/simulate \
      -H 'Content-Type: application/json' \
      -d '{"text_override":"Klinika manzili qayerda?"}'

The response includes the AI reply, `outbound_recording_id`, and `audio` metadata
(voice, content_type, duration_ms, audio_bytes_len, provider). Raw audio bytes are
never returned in the API response.

## Storage
The synthesized audio is stored via `AudioStorageProvider`; the outbound
`AudioRecording` row keeps `tts_text`, `tts_voice`, `content_type`, `size_bytes`,
and `checksum_sha256` (see docs/audio-storage.md). The blob stays out of the DB and
out of the API response.

## CI / tests
CI never calls the real TTS API. Automated tests use a fake OpenAI client
(injected) or the mock provider, so no key and no network are required. The
`openai` SDK is an opt-in extra (`pip install -e ".[tts]"`, same SDK as `[stt]`)
and is not installed for the default test run.

## Remaining gaps
- No streaming TTS (single-shot request/response only).
- OpenAI TTS voices are not locale-specific Uzbek/Russian neural voices; for a
  production clinic pilot, Azure/ElevenLabs neural uz-UZ/ru-RU voices may be
  preferable behind the same `TTSProvider` interface.
- No real telephony; audio still flows through the local simulate bridge, not a
  phone call.
