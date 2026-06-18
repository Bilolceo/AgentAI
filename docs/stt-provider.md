# STT provider (mock + real OpenAI Whisper)

The voice pipeline depends only on `STTProvider`. The provider is selected by
`STT_PROVIDER`. Mock is the default and is the only one used by tests and CI.

## Mock mode (default, no key, deterministic)
`STT_PROVIDER=mock` (default). `MockSTTProvider` resolves the transcript from
`text_hint` (the `text_override` path) > UTF-8 decode of the audio bytes > a
generic fallback. No external calls, no key.

    cd backend
    python -m app.eval.run --suite smoke        # text evals unaffected
    # local voice simulate (mock STT + mock TTS):
    curl -s -X POST http://localhost:8000/api/v1/voice/simulate \
      -H 'Content-Type: application/json' \
      -d '{"text_override":"Klinika manzili qayerda?"}'

## Real STT (OpenAI Whisper) - opt-in
`STT_PROVIDER=openai_whisper`. `RealSTTProvider` lazy-imports the OpenAI SDK and
calls `audio.transcriptions.create` (verbose_json). It returns text + duration;
Whisper has no confidence so `confidence=None`. Language is normalized to our
locale (`uz-UZ`/`ru-RU`), falling back to script detection. The adapter:
- wraps the call in a timeout -> `STTProviderTimeoutError`,
- sanitizes any failure to a type name -> `STTProviderError` (no payload/secret),
- never logs raw audio or the API key.
A failure maps to the safe degraded path (operator transfer, no AI call).

### Env vars
- `STT_PROVIDER=openai_whisper`
- `OPENAI_API_KEY=sk-...`  (required; missing key fails fast at startup)
- `STT_MODEL=whisper-1`
- `STT_TIMEOUT_SECONDS=15`
- `STT_LANGUAGE_HINT=`  (optional ISO-639-1, e.g. `uz` or `ru`)
- `STT_MAX_AUDIO_BYTES=25000000`  (25 MB; oversized -> HTTP 422)
- `STT_ALLOWED_CONTENT_TYPES=...`  (if `content_type` is supplied and not allowed -> 422)

### Install + run (real)
    cd backend
    pip install -e ".[stt]"          # installs the OpenAI SDK (not in default deps)
    export STT_PROVIDER=openai_whisper
    export OPENAI_API_KEY=sk-...
    # send real audio as base64 with its content_type
    B64=$(base64 -i sample.wav | tr -d '\n')
    curl -s -X POST http://localhost:8000/api/v1/voice/simulate \
      -H 'Content-Type: application/json' \
      -d "{\"audio_base64\":\"$B64\",\"content_type\":\"audio/wav\"}"

The response includes the transcript, the AI reply, `inbound_recording_id` /
`outbound_recording_id`, and STT/audio metadata. Raw audio bytes are never
returned.

## Safety + storage
The real transcript flows through the SAME pipeline: `MedicalSafetyGuardService`
runs before the AI provider (unsafe transcripts are blocked/transferred), and the
transcript metadata (text/language/confidence) is saved to `AudioRecording`
(see docs/audio-storage.md).

## CI / tests
CI never calls the real STT API. Automated tests use a fake OpenAI client
(injected) or the mock provider, so no key and no network are required. The
`openai` SDK is an opt-in extra (`pip install -e ".[stt]"`) and is not installed
for the default test run.

## Remaining gaps
- No streaming STT (single-shot request/response only).
- Whisper language labels are mapped heuristically (uz/ru); other languages fall
  back to script detection.
- No real telephony/audio capture; audio still arrives via the local simulate
  bridge, not a phone call. (Real TTS is implemented separately; see
  docs/tts-provider.md.)
