# Streaming STT (mock-first architecture)

This adds a STREAMING speech-to-text architecture on top of the Twilio Media
Streams WebSocket spike. It is ARCHITECTURE + a deterministic MOCK provider only:
- no real speech recognition (the mock does not decode audio),
- no real/paid streaming STT provider (Azure/Deepgram/OpenAI realtime) yet,
- no streaming TTS back to the caller, no barge-in, no AI turn wired into the
  stream.

The non-streaming Twilio Gather/SpeechResult flow, mock telephony, and
`/voice/simulate` are all unchanged.

## Components
- `StreamingAudioFrame` (dataclass): stream_sid, call_sid, sequence_number,
  timestamp_ms, payload_bytes (decoded audio, transient - never logged/persisted),
  codec (default `audio/x-mulaw`), track.
- `TranscriptEvent` (dataclass): text, language, is_final, provider, confidence
  (nullable), timestamp_ms (nullable), metadata (safe dict).
- `StreamingSTTProvider` (interface): `start_stream(context) -> StreamingSTTSession`.
- `StreamingSTTSession` (interface): `accept_audio_frame(frame) -> [TranscriptEvent]`,
  `finish_stream() -> [TranscriptEvent]`, `close()`.
- `MockStreamingSTTProvider`: deterministic. Emits one partial near the middle and
  one final at `STREAMING_STT_FINAL_AFTER_FRAMES` frames. The phrase comes from
  the start event's `customParameters["test_phrase"]` (default `Salom`), so tests
  are fully deterministic without any real audio.
- `StreamingSTTSessionService`: owns one session per stream, counts frames/bytes,
  enforces memory limits, tracks partial/final transcripts, handles provider
  errors safely (marks the session `degraded`, never crashes), and builds a SAFE
  `summary()`.

## Summary (attached to TelephonyStream.stream_metadata.streaming_stt)
Counts + recognized transcript TEXT only - NEVER raw audio or any base64 payload:
- `provider`, `frames_processed`, `bytes_processed`, `partial_count`,
  `final_count`, `final_transcripts` (text/language/confidence), `stopped_reason`
  (stop_event | disconnect | over_limit | finished | degraded), `errors`,
  `degraded`, `over_limit`.
It is visible in `GET /api/v1/admin/telephony-streams/{id}` (super_admin/admin).

## WebSocket integration
In `/api/v1/telephony/twilio/media-stream` (after stream-token auth):
- `start` -> create the TelephonyStream as before; if streaming is enabled, open a
  `StreamingSTTSessionService` (reading `customParameters`).
- `media` -> base64-decode the payload to transient bytes (malformed -> empty,
  never logged), build a `StreamingAudioFrame`, push it to the session, and
  collect partial/final events. The AI is NOT called here (even on a final).
- over limit -> finalize + attach summary + stop + close (1000).
- `stop` / WebSocket disconnect -> finalize the session and attach the summary to
  `stream_metadata` (`stopped_reason` = `stop_event` / `disconnect`).
- A duplicate `start` on the same socket (Twilio sends exactly one) is REJECTED:
  the existing stream/session is finalized (`stopped_reason=superseded`, session
  closed once, no orphan left active) and the socket is closed with a policy
  violation. The media payload is base64-decoded at most ONCE per frame (shared
  helper `decode_media_payload`, with a pre-decode size cap that rejects oversized
  frames before allocating); the decoded bytes are reused for counting and the
  streaming frame.

Streaming runs ONLY when both flags are on (otherwise the WS behaves exactly as
the earlier counting-only spike):
- `TWILIO_USE_MEDIA_STREAMS=true`
- `STREAMING_STT_ENABLED=true`

## Env flags
- `TWILIO_USE_MEDIA_STREAMS` - when true, `/twilio/voice` returns `<Connect><Stream>`.
- `STREAMING_STT_ENABLED` - default false; enable streaming STT on the media stream.
- `STREAMING_STT_PROVIDER=mock` - only `mock` implemented.
- `STREAMING_STT_MAX_FRAMES` (default 10000) - per-stream frame cap; over it the
  socket finalizes + closes safely.
- `STREAMING_STT_MAX_BYTES` (default 8000000) - per-stream byte cap.
- `STREAMING_STT_FINAL_AFTER_FRAMES` (default 25) - mock: emit the final after N
  frames (set small for local tests).

## Testing locally with mock frames
Enable media streams + streaming STT (see docs/twilio-media-streams.md for the
ngrok/wss setup), set `STREAMING_STT_FINAL_AFTER_FRAMES=2`, then connect a
WebSocket client to `/api/v1/telephony/twilio/media-stream` and send:

    {"event":"connected","protocol":"Call","version":"1.0.0"}
    {"event":"start","streamSid":"MZ1","start":{"streamSid":"MZ1","callSid":"CA1",
      "tracks":["inbound"],"mediaFormat":{"encoding":"audio/x-mulaw","sampleRate":8000,"channels":1},
      "customParameters":{"call_sid":"CA1","stream_token":"<signed>","test_phrase":"Klinika manzili qayerda"}}}
    {"event":"media","sequenceNumber":"2","media":{"track":"inbound","payload":"<base64 mu-law>"}}
    {"event":"media","sequenceNumber":"3","media":{"track":"inbound","payload":"<base64 mu-law>"}}
    {"event":"stop","streamSid":"MZ1","stop":{}}

After stop, `GET /api/v1/admin/telephony-streams/{id}` shows
`stream_metadata.streaming_stt` with `final_transcripts: [{"text":"Klinika manzili qayerda", ...}]`.
The `stream_token` is required (signed, expiring) and is never stored/logged.

## What is implemented vs not
Implemented: streaming provider/session interfaces, mock provider, session
service with limits + safe error handling, WebSocket wiring, safe summary,
persistence to stream metadata, admin visibility, full test coverage.

NOT implemented: real streaming STT provider, AI turn on final transcript,
streaming TTS playback, barge-in, turn endpointing, latency metrics.

## Next steps toward a real-time voice pilot
1. Real streaming STT provider (Azure/Deepgram/OpenAI realtime) behind
   `StreamingSTTProvider`, feeding actual mu-law frames.
2. Turn endpointing: detect end-of-utterance to trigger an AI turn through
   `VoicePipelineService` (text-only mode) on a final transcript.
3. Streaming TTS: synthesize the reply and send mu-law `media` frames back over the
   same socket, with `mark` events for playback tracking.
4. Barge-in: stop outbound TTS when inbound speech resumes (`clear` event).
5. Latency + audio-quality metrics and a live voice eval on top of the text evals.
