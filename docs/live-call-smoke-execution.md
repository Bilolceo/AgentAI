# Live-call smoke execution runbook (A32)

The step-by-step procedure to run the FIRST controlled real live call against the
streaming voice pipeline: Twilio + Deepgram STT + Deepgram TTS, behind the A31
smoke-mode gate. This is the execution companion to docs/live-voice-smoke-test.md
(scenario reference) and docs/live-voice-smoke-report-template.md (the form you
fill in).

## Purpose and scope
- Validate, with a handful of STAFF calls, that the real-time pipeline works end to
  end on production infra before any clinic/patient usage.
- NOT a production launch. NOT a public number. NOT an automated provider test.
- A human operator drives every call and records results by hand.

## Rule: no real patient data (mandatory)
Use synthetic scenarios only. Do NOT speak or read back any real patient name,
phone, diagnosis, or record. This is the PRIMARY privacy control;
`LIVE_CALL_REDACT_TRANSCRIPTS` only redacts the streaming metadata summary and does
NOT redact the CallSession transcript rows (see docs/live-voice-smoke-test.md sec 6).

## Commit hash (required)
Record the exact deployed commit before starting:

    git rev-parse HEAD   ->  ____________________

Put this in the report. Do not run the smoke test against an unknown/dirty build.

## Environment checklist (local, before deploy)
- [ ] On the intended commit; `git status` clean.
- [ ] `cd backend && pip install -e ".[stt-streaming]"` (the websockets extra).
- [ ] Offline preflight passes (no network):
      `cd backend && python -m app.scripts.voice_smoke_preflight`
      Exit code 0 = ready; non-zero = fix the listed blocking errors first.
- [ ] Backend tests green: `cd backend && pytest -q`.

## Railway / prod env checklist
Set these as Railway service variables (SECRETS go in Railway secrets, never in
git, never in this doc). Placeholder examples only:

    PUBLIC_BASE_URL=https://<your-app>.up.railway.app
    TELEPHONY_PROVIDER=twilio
    TWILIO_AUTH_TOKEN=<set in Railway secret, never in docs>
    # NOTE: the media-stream stream_token is signed with TWILIO_AUTH_TOKEN.
    # This project has no separate STREAM_TOKEN_SECRET variable.
    TWILIO_USE_MEDIA_STREAMS=true
    TWILIO_STREAM_URL=wss://<your-app>.up.railway.app/api/v1/telephony/twilio/media-stream
    STREAMING_STT_ENABLED=true
    STREAMING_STT_PROVIDER=deepgram
    STREAMING_TTS_ENABLED=true
    STREAMING_TTS_PROVIDER=deepgram
    DEEPGRAM_API_KEY=<set in Railway secret, never in docs>
    LIVE_CALL_SMOKE_MODE=true
    LIVE_CALL_REQUIRE_SMOKE_TOKEN=true
    LIVE_CALL_SMOKE_TOKEN=<long-random-secret, set in Railway secret>
    LIVE_CALL_ALLOWED_CALLER_NUMBERS=<staff-number-only, e.g. +99890XXXXXXX>
    LIVE_CALL_MAX_DURATION_SECONDS=180
    LIVE_CALL_MAX_TURNS=10
    STREAMING_METRICS_ENABLED=true
    BARGE_IN_ENABLED=true
    # Deepgram audio MUST stay Twilio-compatible (defaults already correct):
    DEEPGRAM_ENCODING=mulaw
    DEEPGRAM_SAMPLE_RATE=8000
    DEEPGRAM_TTS_ENCODING=mulaw
    DEEPGRAM_TTS_SAMPLE_RATE=8000
    DEEPGRAM_TTS_CONTAINER=none

- [ ] All secrets are Railway secrets (masked), not plain vars.
- [ ] Redeploy and confirm the service is healthy (`GET /api/v1/health`).

## Twilio setup checklist
- [ ] A Twilio number is owned and Voice-enabled.
- [ ] "A call comes in" webhook = `POST https://<your-app>.up.railway.app/api/v1/telephony/twilio/voice`.
- [ ] The Stream TwiML passes the smoke token via customParameters (NOT the URL):

        <Connect>
          <Stream url="wss://<your-app>.up.railway.app/api/v1/telephony/twilio/media-stream">
            <Parameter name="smoke_token" value="<long-random-secret>"/>
            <Parameter name="from_number" value="{{From}}"/>
          </Stream>
        </Connect>

- [ ] `TWILIO_VALIDATE_SIGNATURE=true` and `PUBLIC_BASE_URL` matches the public host.

## Deepgram setup checklist
- [ ] A Deepgram project + API key exists; key is in the Railway secret only.
- [ ] STT model set (default `nova-2`); language as needed (uz/ru/multi).
- [ ] TTS model set (default `aura-asteria-en`).
- [ ] Audio settings confirmed mu-law / 8000 / container=none (preflight checks this).

## Smoke mode setup
- [ ] `LIVE_CALL_SMOKE_MODE=true`, `LIVE_CALL_REQUIRE_SMOKE_TOKEN=true`.
- [ ] `LIVE_CALL_SMOKE_TOKEN` is a long random secret shared only with the tester's
      TwiML, out of band.
- [ ] `LIVE_CALL_ALLOWED_CALLER_NUMBERS` contains ONLY the staff test number(s).
- [ ] `LIVE_CALL_MAX_DURATION_SECONDS=180`, `LIVE_CALL_MAX_TURNS=10`.

## Readiness endpoint check
Before the first call, confirm the live config from the running service:

    GET https://<your-app>.up.railway.app/api/v1/admin/voice-provider-readiness
    Authorization: Bearer <admin JWT>      # super_admin or admin only

- Admin auth is REQUIRED (operators get 403, anonymous gets 401).
- The output is SAFE: `deepgram_api_key_present` and `smoke_token_present` are
  BOOLEANS (presence only); no key/token value is ever returned.
- If `ready` is false, the `errors[]` list explains why. ready=false BLOCKS the
  live smoke test - resolve every error, redeploy, re-check.

## Exact order of execution
1. Confirm commit hash; `git status` clean.
2. Run the offline preflight locally -> exit 0.
3. Set/confirm Railway env + secrets; redeploy; `/health` ok.
4. Configure the Twilio webhook + Stream TwiML (smoke token in customParameters).
5. Call `GET /admin/voice-provider-readiness` -> `ready: true`.
6. Brief the room (roles below); confirm "no real patient data".
7. Place call 1 (scenario 1). After it ends, capture results (below).
8. Repeat for scenarios 2..10, one call each (or batch as time allows).
9. After the last call, pull each stream's admin detail + latency.
10. Fill in the report template; record the decision (pass / retry / block).
11. ROLLBACK to safe state (below) when finished.

## 10 live-call scenarios (see docs/live-voice-smoke-test.md for prompts/expected)
1. Uzbek clinic working hours.
2. Russian clinic working hours.
3. Service price question.
4. Doctor schedule question.
5. Appointment intent.
6. Operator transfer request.
7. Complaint / angry caller.
8. Emergency / 103.
9. Barge-in while the AI is speaking.
10. Unclear / noisy / empty speech.

## Pass / fail criteria
PASS requires ALL of:
- [ ] Every scenario produced its expected outcome.
- [ ] Emergency spoke the official 103 message; no medical advice anywhere.
- [ ] Medical-advice / unknown price -> operator or safe refusal (no invention).
- [ ] Barge-in interrupted the AI within an acceptable latency.
- [ ] No raw audio, base64, key, token, or phone number in logs/metadata.
- [ ] Duration/turn caps observed where exercised.
- [ ] No crash / stuck stream; every stream reached a clean `stopped_reason`.
Any failure -> RETRY (fix + re-run) or BLOCK (do not pilot).

## Rollback plan (no code change / no deploy needed - env flips)
1. `LIVE_CALL_SMOKE_MODE=false` (re-gate nothing new), OR
2. `TWILIO_USE_MEDIA_STREAMS=false` (revert /twilio/voice to the Gather flow), OR
3. `STREAMING_STT_PROVIDER=mock` / `STREAMING_TTS_PROVIDER=mock` (drop to mock), OR
4. Remove/disable the Twilio number webhook (stop all inbound).
Re-run the readiness check after any change.

## Who should be present
- Test caller (staff) - places calls from an allowlisted number.
- Backend operator - watches logs + admin endpoints, owns rollback.
- Safety reviewer - confirms emergency/operator/no-advice behavior per call.
- (Optional) Note-taker - fills the report template live.

## What to capture after each call
- Scenario number + PASS/FAIL + a short safe note.
- The stream's admin detail: `GET /api/v1/admin/telephony-streams/{id}`:
  - `streaming_stt.provider`, `final_count`, `turns[]` (action / transferred /
    playback), `stopped_reason`.
  - `latency.durations_ms` (record the 8 fields in the report).
- Subjective audio-quality score (1-5) and barge-in score (1-5).

## What must NOT be captured
- No Deepgram key, smoke token, or Twilio token (anywhere).
- No raw caller phone numbers in the report (use counts / masked).
- No raw audio or base64 payloads.
- No real patient data of any kind.

## Troubleshooting
- readiness `ready:false` -> read `errors[]`; fix env; redeploy; re-check.
- WebSocket closes immediately at start -> smoke token mismatch
  (`live_call_smoke_rejected reason=invalid_smoke_token`) or caller not in the
  allowlist (`caller_not_allowed`); the token must be in customParameters, not the
  URL.
- No audio heard -> check `tts_twilio_compatible` (mu-law/8000/container=none) and
  that `STREAMING_TTS_ENABLED=true` + provider=deepgram; a degraded playback shows
  `playback.error` in the turn metadata.
- No transcription -> `STREAMING_STT_ENABLED=true` + provider=deepgram +
  `DEEPGRAM_API_KEY` present; check `streaming_stt.provider=deepgram` and
  `final_count`.
- Stream stops early -> `stopped_reason` `live_call_max_turns` /
  `live_call_max_duration` means a hard cap fired (expected); `over_limit` means a
  frame/byte cap.
- Barge-in not working -> `BARGE_IN_ENABLED=true`; check `barge_in_clear_latency_ms`
  and the turn's `playback.interrupted`.
- 401/403 on readiness -> use a super_admin/admin JWT.

After the run, complete docs/live-voice-smoke-report-template.md and store it
WITHOUT any secret or patient data.
