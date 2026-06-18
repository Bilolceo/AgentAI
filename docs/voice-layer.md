# Voice layer (STT/TTS abstraction + mock stubs)

This adds the voice-layer ARCHITECTURE only. It is NOT real telephony: there is
no SIP/Twilio, no phone calls, and no audio streaming yet. The voice layer is a
local bridge between future audio and the existing text pilot, so the safety/AI
behavior stays identical.

## Components
- `STTProvider` (interface) + `STTResult` (text, language, confidence,
  duration_ms, provider_metadata). `MockSTTProvider` is deterministic:
  `text_hint` (the `text_override` path) > UTF-8 decode of the audio bytes > a
  generic fallback. Errors: `STTProviderError`, `STTProviderTimeoutError`.
- `TTSProvider` (interface) + `TTSResult` (audio_bytes, audio_url, text,
  language, voice, content_type, duration_ms, provider_metadata).
  `MockTTSProvider` returns deterministic fake audio (`b"MOCK-AUDIO:" + text`),
  never calls anything. `RealTTSProvider` (OpenAI TTS) is opt-in via
  `TTS_PROVIDER=openai_tts` (see docs/tts-provider.md). Errors:
  `TTSProviderError`, `TTSProviderTimeoutError`.
- `VoicePipelineService`: audio bytes -> STT -> `CallSessionService` (full safety
  pipeline + AI + transfer engine) -> TTS. A provider failure/timeout (STT or
  TTS) maps to a safe operator transfer; the text safety pipeline is unchanged.

## Config (.env)
- `STT_PROVIDER=mock` (default) or `openai_whisper` (opt-in; see docs/stt-provider.md)
- `TTS_PROVIDER=mock` (default) or `openai_tts` (opt-in; see docs/tts-provider.md)
- `STT_TIMEOUT_SECONDS`, `TTS_TIMEOUT_SECONDS`
- `DEFAULT_VOICE_UZ`, `DEFAULT_VOICE_RU` (+ `TTS_VOICE_UZ`/`TTS_VOICE_RU` for OpenAI TTS)

No keys are needed for mock mode. The real STT adapter (OpenAI Whisper,
`STT_PROVIDER=openai_whisper`) and the real TTS adapter (OpenAI TTS,
`TTS_PROVIDER=openai_tts`) are both implemented and opt-in.

## Local voice simulation endpoint (not telephony)
`POST /api/v1/voice/simulate` - bridges a fake audio/text input through the
voice pipeline. Provide one of `text_override` (deterministic) or `audio_base64`
(base64 of bytes; the mock STT decodes UTF-8). Optional `call_id` continues an
existing call; otherwise a new call is started.

    curl -s -X POST http://localhost:8000/api/v1/voice/simulate \
      -H 'Content-Type: application/json' \
      -d '{"text_override":"Klinika manzili qayerda?"}'

    # emergency -> 103, TTS still voices the safe message
    curl -s -X POST http://localhost:8000/api/v1/voice/simulate \
      -H 'Content-Type: application/json' \
      -d '{"text_override":"Nafas ololmayapman"}'

    # fake audio payload (base64 of "Ish vaqtingiz qanday?")
    curl -s -X POST http://localhost:8000/api/v1/voice/simulate \
      -H 'Content-Type: application/json' \
      -d '{"audio_base64":"SXNoIHZhcXRpbmdpeiBxYW5kYXk/"}'

Response includes: call_id, transcript, ai_text, action, reason_code,
transferred, language, transfer_reason, sources, plus `stt` and `audio`
metadata (no raw audio bytes are returned).

## Real / future providers
- STT: OpenAI Whisper is implemented (opt-in; docs/stt-provider.md). Deepgram /
  Yandex SpeechKit can follow behind the same `STTProvider` interface.
- TTS: OpenAI TTS is implemented (opt-in; docs/tts-provider.md). ElevenLabs /
  Azure / Yandex SpeechKit can follow behind the same `TTSProvider` interface.
Each is added behind `STTProvider`/`TTSProvider` with `asyncio.wait_for` timeouts
mapping to the same safe-transfer fallback. Selection stays via
`STT_PROVIDER`/`TTS_PROVIDER`.

## Next steps toward a real voice pilot
1. Audio storage (recordings + synthesized audio; signed URLs) and returning
   `audio_url` instead of inline bytes.
2. Telephony intake (Twilio/SIP) + media streaming (WebSocket), barge-in, and
   turn endpointing.
3. Streaming STT/TTS (partial transcripts, low-latency synthesis) rather than the
   current single-shot request/response.
4. Real provider implementations + a live voice eval (latency, audio quality,
   transcription accuracy) on top of the existing text evals.
