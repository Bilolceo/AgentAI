# Twilio Voice webhook (non-streaming Gather/SpeechResult)

The first REAL Twilio-compatible inbound flow: signature validation, Voice webhook
form parsing, and valid TwiML for a basic conversation loop built on Twilio's
built-in speech-to-text (`SpeechResult`) and `<Say>` text-to-speech.

This is NOT Media Streams. There are no WebSocket audio frames, no barge-in, no
streaming STT/TTS, and no outbound dialing. Speech text comes in; AI text goes out.

`/voice/simulate` and the mock telephony provider are unchanged.

## Flow
1. Twilio POSTs the inbound call to `POST /api/v1/telephony/twilio/voice`:
   - validate `X-Twilio-Signature`,
   - start a `CallSession` (greeting) and create a `TelephonyCall` (provider=twilio,
     provider_call_id=CallSid),
   - return TwiML: a greeting inside a `<Gather input="speech">` whose `action`
     points to `/twilio/gather`; if no speech is captured it says a short message
     and hangs up.
2. Twilio POSTs the recognized speech to `POST /api/v1/telephony/twilio/gather`:
   - validate signature, parse `SpeechResult`,
   - if `SpeechResult` is empty -> TwiML asking the caller to repeat (re-Gather),
   - else run `VoicePipelineService` with `text_override=SpeechResult` (full
     medical-safety + AI + transfer engine),
   - normal answer -> TwiML that `<Say>`s the AI reply then `<Gather>`s the next
     question,
   - transfer/emergency -> TwiML that `<Say>`s the safe operator/emergency message
     then `<Hangup/>` (no re-Gather; no Dial in this spike).
3. Optional `POST /api/v1/telephony/twilio/status` updates the `TelephonyCall`
   status from `CallStatus` and returns an empty `<Response/>`.

All three endpoints are public but reject requests whose `X-Twilio-Signature`
does not validate (HTTP 403) when validation is enabled.

## Signature validation
`X-Twilio-Signature = base64(HMAC-SHA1(auth_token, url + sorted(k+v)))` over the
POST params. The server reconstructs `url` from `PUBLIC_BASE_URL + request path`,
so `PUBLIC_BASE_URL` MUST equal the public URL configured in the Twilio console
(scheme + host, no trailing slash). Comparison uses `hmac.compare_digest`
(constant-time). The auth token is never logged; the signature is never echoed in
errors or stored in metadata.

Tests inject a fake validator (or use the deterministic HMAC helper), so no real
Twilio account, token, or network is required. No Twilio SDK is needed: the HMAC
is computed with the Python standard library, and `python-multipart` (already a
dependency) parses the form body.

## Env vars
- `TELEPHONY_PROVIDER=twilio` (opt-in; default is `mock`).
- `TWILIO_AUTH_TOKEN` (required; missing -> fail fast at startup).
- `TWILIO_ACCOUNT_SID` (optional).
- `TWILIO_VALIDATE_SIGNATURE=true` (default). When true, `PUBLIC_BASE_URL` is
  required (fail fast if empty).
- `PUBLIC_BASE_URL` (e.g. your https ngrok URL).
- `TWILIO_VOICE=alice`, `TWILIO_GATHER_LANGUAGE=ru-RU`,
  `TWILIO_GATHER_TIMEOUT_SECONDS=5`.

## Local testing with ngrok
    # 1) run the backend
    cd backend && uvicorn app.main:app --port 8000
    # 2) expose it publicly
    ngrok http 8000
    # 3) set PUBLIC_BASE_URL to the ngrok https URL and TELEPHONY_PROVIDER=twilio
    #    (PUBLIC_BASE_URL must match exactly what Twilio will call)

### Twilio console webhook URLs
- A Number -> Voice -> "A call comes in":
  `https://<your-ngrok>.ngrok.io/api/v1/telephony/twilio/voice`  (HTTP POST)
- Status callback (optional):
  `https://<your-ngrok>.ngrok.io/api/v1/telephony/twilio/status` (HTTP POST)
The Gather `action` (`/twilio/gather`) is emitted by the server in the TwiML, so
you do not configure it in the console.

## Local curl (fake-signature / disabled-validation mode)
Real Twilio signs requests; for a quick local check, run with
`TWILIO_VALIDATE_SIGNATURE=false` (NEVER do this in production) and POST a
form-encoded body:

    # incoming voice -> greeting + Gather TwiML
    curl -s -X POST http://localhost:8000/api/v1/telephony/twilio/voice \
      -H 'Content-Type: application/x-www-form-urlencoded' \
      --data 'CallSid=CA-demo&From=%2B998901112233&To=%2B998711111111'

    # gather result -> AI answer + Gather TwiML
    curl -s -X POST http://localhost:8000/api/v1/telephony/twilio/gather \
      -H 'Content-Type: application/x-www-form-urlencoded' \
      --data 'CallSid=CA-demo&SpeechResult=Klinika%20manzili%20qayerda%3F'

With signature validation ENABLED, compute a valid `X-Twilio-Signature` from the
auth token + the public URL + sorted params (Twilio does this for you in prod).

## Example TwiML responses
Greeting (from `/twilio/voice`):

    <?xml version="1.0" encoding="UTF-8"?><Response><Gather input="speech" method="POST" action="https://example.test/api/v1/telephony/twilio/gather" language="ru-RU" speechTimeout="auto" timeout="5"><Say voice="alice" language="ru-RU">[greeting]</Say></Gather><Say voice="alice" language="ru-RU">Javob eshitilmadi. Iltimos keyinroq qayta qo'ng'iroq qiling.</Say><Hangup/></Response>

Answer (from `/twilio/gather`, normal reply):

    <?xml version="1.0" encoding="UTF-8"?><Response><Say voice="alice" language="ru-RU">[AI reply]</Say><Gather input="speech" method="POST" action="https://example.test/api/v1/telephony/twilio/gather" language="ru-RU" speechTimeout="auto" timeout="5"><Say voice="alice" language="ru-RU">Yana savolingiz bo'lsa, ayting.</Say></Gather><Say voice="alice" language="ru-RU">Qo'ng'iroq uchun rahmat. Sog' bo'ling.</Say><Hangup/></Response>

Operator/emergency (from `/twilio/gather`, transfer/emergency):

    <?xml version="1.0" encoding="UTF-8"?><Response><Say voice="alice" language="ru-RU">[safe operator/emergency message]</Say><Hangup/></Response>

All `<Say>` text is XML-escaped; no raw provider error is ever put into TwiML.

## Security notes
- Constant-time signature comparison (`hmac.compare_digest`).
- Auth token never logged; signature never stored or echoed.
- `raw_metadata` keeps only a safe subset of form fields and is additionally
  redacted on admin read (secret/token/signature -> `[REDACTED]`).
- Unexpected pipeline errors return a generic error TwiML, not a traceback.

## Media Streams toggle (spike)
A first Media Streams WebSocket spike now exists. Set
`TWILIO_USE_MEDIA_STREAMS=true` + `TWILIO_STREAM_URL=wss://.../api/v1/telephony/twilio/media-stream`
and `/twilio/voice` returns `<Connect><Stream>` instead of the Gather flow. The
WebSocket parses connected/start/media/stop events and counts frames/bytes only -
it does NOT yet do streaming STT/TTS or barge-in. See docs/twilio-media-streams.md.

When `TWILIO_USE_MEDIA_STREAMS=false` (default), this Gather/SpeechResult flow is
unchanged.

## Next step: streaming STT/TTS
Build streaming STT (partial transcripts) + turn endpointing on top of the media
stream, then streaming TTS back over the socket, plus barge-in - behind the same
`TelephonyProvider` interface. See docs/twilio-media-streams.md.
