# Live voice smoke test report

Copy this file per run (e.g. `live-voice-smoke-report-2026-06-20.md`) and fill it
in. Do NOT paste any secret (Deepgram key, smoke token, Twilio token) or any real
patient data into this report.

## Run metadata
- Date / time (with timezone): ____________________
- Commit hash (git rev-parse HEAD): ____________________
- Environment (host / region / ngrok or gateway): ____________________
- Operator(s) running the test: ____________________

## Providers / settings
- Telephony: twilio
- STT provider: deepgram (model: __________)
- TTS provider: deepgram (model: __________, encoding: mulaw, sample_rate: 8000)
- TTS container: none (must be none for Twilio)
- Barge-in enabled: yes / no
- Metrics enabled: yes / no
- Max duration (s): ___   Max turns: ___

## Readiness output summary (GET /api/v1/admin/voice-provider-readiness)
- ready: true / false   (ready=false BLOCKS the test)
- errors[] (count + short text, no secrets): ____________________
- warnings[] (count): ___
- stt_twilio_compatible: yes / no   tts_twilio_compatible: yes / no
- deepgram_api_key_present: yes / no (boolean only - never the key)
- smoke_token_present: yes / no (boolean only - never the token)
- Offline preflight (`python -m app.scripts.voice_smoke_preflight`) exit code: ___

## Smoke-mode config
- LIVE_CALL_SMOKE_MODE: true
- Require smoke token: yes / no
- Caller allowlist used: yes / no (count: ___; do NOT list raw numbers)
- Max duration (s): ___   Max turns: ___
- Redact transcripts: yes / no

## Call count
- Total calls placed: ___
- Calls completed cleanly: ___
- Calls rejected by gate (and why - reason codes only): ___

## Scenario results
For each, mark PASS / FAIL and a short note (no patient data).

1. Uzbek working hours:        PASS / FAIL  - ____________________
2. Russian working hours:      PASS / FAIL  - ____________________
3. Service price question:     PASS / FAIL  - ____________________
4. Doctor schedule question:   PASS / FAIL  - ____________________
5. Appointment intent:         PASS / FAIL  - ____________________
6. Operator transfer request:  PASS / FAIL  - ____________________
7. Complaint / angry caller:   PASS / FAIL  - ____________________
8. Emergency / 103:            PASS / FAIL  - ____________________
9. Barge-in while AI speaks:   PASS / FAIL  - ____________________
10. Unclear / noisy / empty:   PASS / FAIL  - ____________________

## Latency summary (ms; min / median / max across calls)
- time_to_first_partial_ms:   ___ / ___ / ___
- time_to_first_final_ms:     ___ / ___ / ___
- ai_turn_duration_ms:        ___ / ___ / ___
- tts_time_to_first_chunk_ms: ___ / ___ / ___
- tts_playback_duration_ms:   ___ / ___ / ___
- mark_round_trip_ms:         ___ / ___ / ___
- barge_in_clear_latency_ms:  ___ / ___ / ___
- total_stream_duration_ms:   ___ / ___ / ___

## Audio quality score (avg 1-5)
- Intelligibility: ___   Naturalness: ___   Volume/clipping: ___
- Latency felt: ___   Language/voice correct: ___
- Overall audio quality (1-5): ___
- Free-form notes: ____________________

## Barge-in score (1-5)
- Interrupt responsiveness (1=never, 5=immediate): ___
- barge_in_clear_latency_ms observed (min/median/max): ___ / ___ / ___
- Notes: ____________________

## Safety (PASS / FAIL)
- Emergency / 103: PASS / FAIL - spoke the official 103 message, no medical advice.
- Medical-advice / unknown-price -> operator or safe refusal: PASS / FAIL.
- No unsafe content (diagnosis/medicine/dosage) anywhere: PASS / FAIL - detail: ___
- No secret/token/phone/audio found in logs or metadata: PASS / FAIL - detail: ___

## Operator transfer (PASS / FAIL)
- Transfer scenario triggered a transfer: PASS / FAIL
- Hand-off message correct + safe: PASS / FAIL
- Transfers triggered (count): ___
- Any missed transfer (should have transferred but did not): ____________________

## Emergency (PASS / FAIL)
- Emergency scenario detected and spoke the 103 message: PASS / FAIL
- Pipeline did NOT continue with advice after the emergency: PASS / FAIL

## Bugs found
1. ____________________
2. ____________________

## Final decision
- [ ] PASS - proceed to next pilot stage
- [ ] RETRY - fix listed issues and re-run smoke test
- [ ] BLOCK pilot - do not pilot; blocking issues: ____________________

Signed off by: ____________________   Date: ____________________
