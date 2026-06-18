# Next Implementation Roadmap → TZ Pilot Acceptance

Goal: get from the current **text-simulation foundation** to **TZ Pilot
Acceptance (§13.1)**. Strategy: finish everything that does **not** need external
providers first (logic parity in the text sim), then add the voice layer once
Discovery data + provider credentials arrive.

Two tracks run in this order:
- **Track A — Logic parity (no providers needed).** Buildable now.
- **Track B — Voice pilot (blocked).** Needs Discovery §18 + provider creds.

---

## Dependencies that gate everything (resolve in parallel)
- **D1 — Discovery data (§18):** clinic info, doctors, services/prices, ≥30 FAQ,
  operators list, official medical-safety/answer policy. → blocks real KB + eval calls.
- **D2 — Provider credentials:** SIP/Twilio, Whisper (STT), TTS. → blocks Track B.
- **D3 — Decision:** confirm Track A (hardened text sim) is the agreed internal
  milestone before voice. (CLAUDE.md says yes; TZ §13.1 is voice — align with client.)

---

## Track A — Logic parity in the text simulation (do now)

### A1. Complete the medical-safety guard (CRITICAL) — gap §3
- Add categories: **patient-data disclosure** and **negative talk about other
  clinics/doctors** to `SafetyGuardService`.
- Strengthen uz/ru keyword coverage (Cyrillic uz, transliteration, typos) from D1 policy doc.
- Add an **LLM-side safety re-check** in `AIService` (post-generation guard) so a
  bypassed keyword still can't emit advice.
- Tests: data-disclosure, negative-talk, paraphrase/typo bypass, prompt-injection.
- **Done when:** new safety tests pass; no path reaches the user with medical advice.

### A2. Operator-transfer decision engine — gap §4
- New `TransferDecisionService` (or extend `OperatorTransferService`) covering all
  §4.6 triggers: explicit "operator" request, complaint, low confidence,
  price/schedule unclear, angry caller, operator-busy → **callback task**.
- Add `CallbackTask` model + audit `operator_transfer_requested` with reason.
- Tests: one per trigger; assert `transferred=true` + reason + (busy) callback row.
- **Done when:** §13.1 "10 transfers" cases are reproducible in the sim.

### A3. Greeting + language flow — gap §2
- Add an AI greeting on `start_call` (uz/ru) and return it in the start response.
- Improve `detect_language` (handle Cyrillic-uz / mixed) or detect from first turn.
- Tests: greeting present per language; detection cases.

### A4. Structured Knowledge Base + admin CRUD — gap §1/§6
- Model clinic info / services+prices / doctors / FAQ / prep-instructions (KB categories §8.4).
- `POST/PUT/DELETE /knowledge` no-code CRUD; keep keyword search (RAG is Standard).
- Seed from D1. Tests: retrieval returns seeded answers; "price unclear → transfer".
- **Done when:** info/services/doctor questions answered from real seeded KB.

### A5. Admin dashboard data views — gap §6
- Frontend pages: `/calls` (history + filters), call detail (transcript view),
  `/knowledge` (CRUD), `/bookings`. Wire to existing admin API with `X-API-Key`.
- Main dashboard metrics (§8.1): calls today, AI-handled %, transfers, agent status.
- **Done when:** a reviewer can open a call and read its full transcript (the §13.1
  "transcripts visible/downloadable" criterion, minus audio).

### A6. Auth, roles, audit-on-admin — gap §8
- Replace `X-API-Key` with user login + roles (Super Admin / Admin / Operator, §8.5).
- 2FA for admin (§10.1). Invoke `AuditLogService` on every admin mutation.
- Tests: role enforcement (operator can't edit KB), admin action audited.

### A7. Pilot evaluation harness — gap §10
- A scripted test set (uz/ru) of representative questions with expected
  category/transfer outcomes → measures "≥80% correct" against the sim.
- Concurrency smoke test (2 parallel sessions).
- **Done when:** a repeatable report shows pass-rate + transfer timing.

**Exit criteria for Track A:** safety complete + all transfer triggers + greeting +
real seeded KB + admin transcript view + roles/audit + eval harness green.

---

## Track B — Voice pilot (after Track A + D1 + D2)

### B1. Telephony intake (Twilio/SIP) — webhook → call record + greeting (TTS).
### B2. STT (Whisper) streaming → feed transcripts into the **same** `AIService`.
### B3. TTS (ElevenLabs/OpenAI) → speak replies; uz/ru voices.
### B4. Audio recording + storage (S3/R2); link to call; admin download (§8.2/§13.1).
### B5. Live operator transfer (call bridging) + callback queue execution.
### B6. Latency instrumentation (target 1.5–3s, §9); 1–2 parallel-call load test.

> Reuse: `AIService`, `SafetyGuardService`, `CallSessionService`, transcripts, audit
> are provider-agnostic — voice plugs in at the edges, business logic unchanged.

**Exit criteria for Track B = TZ §13.1 Pilot Acceptance:** 50 calls ≥80%, 10
transfers ≤30s, 2 parallel, 15 uz + 15 ru (native eval), 50 transcripts+audio in
admin, operator participation.

---

## Cross-cutting (do alongside, before production)
- **Deploy/Sec (§10):** TLS 1.3 (Let's Encrypt) at nginx; secrets via env (done);
  retention + export/delete jobs (§10.2/§10.3); CI (`pytest` on push).
- **Out of Pilot (Standard, §14.1):** RAG/pgvector, Google Calendar/CRM booking,
  SMS/Telegram reminders, monitoring (Sentry/Grafana). Do **not** pull into Pilot.

---

## Suggested order
1. **A1 safety** (critical, no deps) → **A2 transfers** → **A3 greeting**.
2. In parallel, request **D1 Discovery** → **A4 KB seed** → **A7 eval harness**.
3. **A5 admin views** → **A6 auth/roles**.
4. Gate review: Track A exit criteria met?
5. With **D2 creds**: **Track B** voice pilot → §13.1 acceptance.
