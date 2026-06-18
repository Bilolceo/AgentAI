# Telephony intake (spike)

A telephony intake ABSTRACTION plus a safe local/mock webhook flow so future
Twilio/SIP integration can plug into the existing `VoicePipelineService` without
touching the text safety pipeline. This is a SPIKE, not production telephony:
- no real Twilio account required, no paid calls,
- no real-time media streaming, no barge-in, no outbound dialing,
- mock is the default; Twilio is a config + signature-validation SKELETON only.

`/voice/simulate` is unchanged; telephony is an additional intake surface that
ends up calling the same pipeline.

## Components
- `TelephonyProvider` (interface): `validate_inbound_request(headers, body)`,
  `parse_inbound_call(headers, body) -> InboundCallEvent`,
  `build_voice_response(outcome) -> VoiceResponse`, and a `parse_media_event`
  stub (raises NotImplementedError). Errors: `TelephonySignatureError`,
  `TelephonyParseError`.
- `MockTelephonyProvider` (default): accepts a JSON webhook body, optionally
  authenticates a shared secret via the `X-Telephony-Secret` header, and
  normalizes the payload into an `InboundCallEvent`. Deterministic, no network.
- `TwilioTelephonyProvider` (real, non-streaming): validates `X-Twilio-Signature`
  (HMAC-SHA1, constant-time), parses the Voice webhook form, and builds valid
  TwiML for a Gather/SpeechResult conversation loop. Opt-in via
  `TELEPHONY_PROVIDER=twilio`; fails fast without `TWILIO_AUTH_TOKEN` (and without
  `PUBLIC_BASE_URL` when signature validation is enabled). It does NOT do Media
  Streams / WebSocket audio / barge-in / outbound dialing. See docs/twilio-webhook.md.
- `TelephonyIntakeService`: validate -> parse -> persist `TelephonyCall` ->
  run `VoicePipelineService` -> update status -> build response. Audits
  `telephony_call_started` and `telephony_call_processed`.
- `TelephonyCall` model/table (migration `0010_telephony_calls`): provider,
  provider_call_id, call_session_id, from/to_number, status
  (received|processed|failed), direction, raw_metadata (SAFE subset only),
  started_at/ended_at/created_at/updated_at.

## Config (.env)
- `TELEPHONY_PROVIDER=mock` (default) or `twilio` (skeleton).
- `TELEPHONY_WEBHOOK_SECRET` (optional): when set, the mock webhook requires the
  `X-Telephony-Secret` header to match.
- `TELEPHONY_MAX_PAYLOAD_BYTES=1000000`: oversized webhook body -> HTTP 422.
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `PUBLIC_BASE_URL`: used by the Twilio
  skeleton (no real calls).

## Endpoints
- `POST /api/v1/telephony/webhook` - provider-configured inbound webhook. Public,
  but the provider authenticates the request (mock secret / Twilio signature).
- `POST /api/v1/telephony/mock/inbound` - local-testing entrypoint that always
  uses the mock provider (handy even if TELEPHONY_PROVIDER=twilio).
- `POST /api/v1/telephony/twilio/voice` - real Twilio Voice webhook (greeting +
  Gather TwiML). See docs/twilio-webhook.md.
- `POST /api/v1/telephony/twilio/gather` - Twilio Gather callback (runs the
  pipeline on SpeechResult, returns answer/operator TwiML).
- `POST /api/v1/telephony/twilio/status` - optional Twilio status callback.
- `GET /api/v1/admin/telephony-calls?provider=&status=&direction=&call_session_id=&limit=&offset=`
  - list intake records (super_admin/admin only; operator 403; unauth 401).
- `GET /api/v1/admin/telephony-calls/{id}` - one intake record.

No raw audio bytes are ever returned. The admin response carries only safe
metadata; the audio metadata in the webhook response is length + provider, not
bytes. `raw_metadata` is additionally passed through the audit redactor on read,
so any sensitive-looking key (secret/token/signature/...) is `[REDACTED]`.

## Admin UI
`/admin/telephony-calls` (nav link shown to super_admin/admin only):
- Filter by provider, status, direction, and call_session_id; prev/next
  pagination (page size 25). Loading / empty / error states.
- Table columns: id, provider, provider_call_id, status, direction, from_number
  (masked), to_number (masked), call_session_id, started_at, created_at.
- Detail view `/admin/telephony-calls/[id]`: full safe details (provider,
  provider_call_id, status, direction, from/to_number, call_session_id,
  started/ended/created/updated) and the redacted `raw_metadata` as
  preformatted JSON. When `call_session_id` is set it links to the call detail
  (`/admin/calls/[id]`) and to the filtered audio recordings page
  (`/admin/audio-recordings?call_id=...`).
- Operators visiting either page see a forbidden message (and the backend
  returns 403). The nav link is hidden for operators.

## Mock webhook flow
1. Validate payload size (`TELEPHONY_MAX_PAYLOAD_BYTES`).
2. Authenticate the secret if configured (else allow).
3. Parse JSON into an `InboundCallEvent` (needs `text_override` or `audio_base64`).
4. Create a `TelephonyCall` (status=received) and audit `telephony_call_started`.
5. Run `VoicePipelineService` (full safety + AI + transfer; STT/TTS via providers;
   audio recordings saved when storage is wired).
6. Update the `TelephonyCall` (status=processed, link call_session_id, safe
   outcome metadata) and audit `telephony_call_processed`.
7. Return the provider response payload (ai_text + audio metadata).

### Error mapping
- invalid signature/secret -> 403
- provider parse error / missing text+audio / bad base64 -> 400
- oversized payload -> 422
- provider not implemented (Twilio paths) -> 501
- unexpected pipeline failure -> 500 (generic; never a raw traceback)

## Local curl example
    # text payload (deterministic)
    curl -s -X POST http://localhost:8000/api/v1/telephony/mock/inbound \
      -H 'Content-Type: application/json' \
      -d '{"provider_call_id":"mock-1","from_number":"+998901112233",
           "text_override":"Klinika manzili qayerda?"}'

    # with a configured secret
    curl -s -X POST http://localhost:8000/api/v1/telephony/mock/inbound \
      -H 'Content-Type: application/json' \
      -H 'X-Telephony-Secret: the-secret' \
      -d '{"text_override":"Ish vaqtingiz qanday?"}'

    # fake audio payload (base64 of "Ish vaqtingiz qanday?")
    curl -s -X POST http://localhost:8000/api/v1/telephony/mock/inbound \
      -H 'Content-Type: application/json' \
      -d '{"audio_base64":"SXNoIHZhcXRpbmdpeiBxYW5kYXk/","content_type":"audio/wav"}'

The response includes `call_session_id`, `ai_text`, `action`, `transferred`,
`language`, and `audio` metadata (no raw bytes).

## Twilio — implemented vs not
Implemented (see docs/twilio-webhook.md): `X-Twilio-Signature` HMAC-SHA1
verification, Voice webhook form parsing, valid TwiML, and a non-streaming
Gather/SpeechResult conversation loop into `VoicePipelineService`.

NOT implemented yet: `<Connect><Stream>` Media Streams, WebSocket audio frames,
streaming STT/TTS, barge-in, and outbound dialing. The generic JSON
`/telephony/webhook` is not used for Twilio (Twilio uses the dedicated
`/telephony/twilio/*` endpoints).

## CI / tests
CI never calls a real telephony provider. Tests use the mock provider and the
in-process ASGI client; no Twilio account, token, or network is required.
Provider validation reasons never echo the secret.

## Next steps toward a real Twilio/SIP pilot
1. Real Twilio signature validation (HMAC-SHA1 over URL + sorted params) and
   form parsing; return real TwiML.
2. Media streaming: `<Connect><Stream>` over WebSocket, frame decode (mu-law),
   and turn endpointing.
3. Streaming STT/TTS (partial transcripts, low-latency synthesis) instead of the
   current single-shot request/response.
4. Barge-in (interrupt TTS on caller speech) and call-control (hold/transfer).
5. Latency + audio-quality metrics and a live voice eval on top of the text evals.
6. SIP trunk option behind the same `TelephonyProvider` interface.
