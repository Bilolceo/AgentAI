# TZ Gap Analysis — v2.1 vs current code

Source: `docs/TZ_AI_CallCenter_v2.1.md` (extracted from the docx). Compared against
the code in `backend/` + `frontend/` and the test suite (`backend/app/tests/`,
24 passing). **Nothing is marked "done" unless code _and_ a test prove it.**

Status legend: **done · partial · missing · risky · blocked**

---

## 0. The big framing gap (read first)

| Topic | TZ says | Current build | Status |
|---|---|---|---|
| What "Pilot MVP" is | §12.2 / §13.1: **voice** pilot — inbound calls, STT/TTS, **audio** recordings, 50 live test calls | **text-based** simulation only (`/simulation/*`), no voice, no audio | **partial** — current = pre-pilot foundation, not the TZ Pilot |
| RAG | §14.1: RAG is **Standard**, Pilot KB is "asosiy" (basic) | keyword ILIKE search (`RAGService`) | **done for Pilot** (RAG/pgvector is Standard, not required now) |
| Booking + Calendar | §14.1/§12.3: booking & Google Calendar are **Standard** | basic `Booking` model + admin endpoint exists | **head-start** (not Pilot-required; CLAUDE.md added a "basic model") |

> Consequence: reaching **TZ Pilot Acceptance (§13.1)** requires voice + audio +
> an admin panel that shows/downloads transcripts — none of which the text
> simulation delivers yet. CLAUDE.md's text-sim is a valid internal milestone,
> but it is **not** the deliverable §13.1 tests.

---

## 1. AI scenarios (§4)

| TZ requirement | Code | Test proof | Status |
|---|---|---|---|
| §4.1 Clinic info (address, hours, contacts) | KB keyword search returns chunks | `test_ai_service` (KB answer via stub) | **partial** — engine works, **no real clinic data** (needs Discovery §18) |
| §4.2 Services & prices; defer to operator if price unclear | not modeled; no "price unclear → transfer" | — | **missing** |
| §4.3 Doctors (FIO, specialty, schedule, free slots) | no doctor/schedule model | — | **missing** |
| §4.4 Booking flow (check availability → propose 2–3 slots → confirm name/phone → write Calendar → SMS) | basic `Booking.create` only; no slots, no confirm, no calendar | `test_booking` (row creation only) | **missing** (Standard scope; partial head-start) |
| §4.5 Modify/cancel booking | not implemented | — | **missing** (Standard) |
| §4.6 Operator-transfer conditions (8 cases) | only safety-driven transfer (medical-advice + emergency) | `test_call_session` (emergency transfer) | **partial** — see §3 below |

## 2. Greeting & language (§3.1, §6.2)

| TZ requirement | Code | Test proof | Status |
|---|---|---|---|
| AI greeting at call start (uz/ru) | none — text sim has no greeting turn | — | **missing** |
| Detect caller language, answer in it | `detect_language()` Cyrillic→ru else uz | `test_call_session::test_russian_language_detected` | **partial** — heuristic only (no mixed/transliterated uz, no STT-driven detection) |

## 3. Medical safety (§5) — **CRITICAL**

| TZ §5.1 forbidden action | Covered in `SafetyGuardService`? | Test proof | Status |
|---|---|---|---|
| No diagnosis | yes (`DIAGNOSIS`) | `test_safety` | **done** |
| No disease guessing | partial (folds into diagnosis) | partial | **partial** |
| No medicine recommendation | yes (`MEDICINE`) | `test_safety` | **done** |
| No dosage advice | yes (`DOSAGE`) | `test_safety` | **done** |
| No treatment plan | yes (`TREATMENT`) | `test_safety` | **done** |
| **No disclosing patient data to third parties** | **not modeled** | — | **missing** |
| **No negative talk about other clinics/doctors** | **not modeled** | — | **missing** |
| Don't waste time during emergency (stop flow) | yes — emergency short-circuits | `test_safety`, `test_ai_service` | **done** |
| §5.2 verbatim emergency message | exact match (uz) + ru variant | `test_safety` (uz & ru) | **done** |

**Risky:** the guard is **keyword-based** (Latin-script uz + ru lists). TZ rates
medical-safety risk **"Kritik"** and requires prompt-injection resistance (§17).
Keyword coverage is partial and easy to bypass with paraphrase/typos; there is no
test for data-disclosure or negative-talk, and no LLM-side safety re-check.

## 4. Operator transfer (§4.6) — required for Pilot (§13.1: 10 transfers ≤30s)

| TZ trigger | Code | Status |
|---|---|---|
| Explicit "operatorga ulang" request | not detected (would be treated as normal turn) | **missing** |
| Medical-advice-adjacent | yes (safety → transfer) | **done** |
| Complaint | not detected | **missing** |
| Low AI confidence | no confidence signal from provider | **missing** |
| Price/schedule unclear | not detected | **missing** |
| Emergency → 103 + transfer | yes | **done** |
| Angry caller | not detected | **missing** |
| Operator busy → save number, create callback task | no callback task model | **missing** |

`OperatorTransferService.request_transfer` only flips `call.status="transferred"`
+ audit. No SLA/timing (TZ: ≤30s), no callback queue.

## 5. Architecture & components (§6.1)

| Component | TZ tech | Current | Status |
|---|---|---|---|
| Telephony | Twilio/SIP | none (text sim) | **blocked** (providers + CLAUDE.md gate) |
| STT | Whisper | none | **blocked** (Pilot needs it; deferred by design) |
| LLM | Claude Sonnet | `ClaudeAIProvider` (lazy), MockAIProvider default | **partial** — not validated against a live KB |
| RAG/KB | Qdrant+embeddings (Standard) | pgvector model + keyword search | **done for Pilot** |
| TTS | ElevenLabs/OpenAI | none | **blocked** |
| Orchestration | FastAPI | FastAPI app, services, `import app.main` OK (15 routes) | **done** |
| Admin panel | React/Next | Next.js scaffold + simulation chat | **partial** (no admin data views) |
| Notification | SMS/Telegram (Standard) | `NotificationService` mock/log | **head-start** (Standard scope) |

## 6. Admin dashboard (§8) — Pilot needs "asosiy" + transcripts (§13.1)

| TZ requirement | Code | Status |
|---|---|---|
| §8.1 Main metrics (calls today, AI-handled %, transfers, bookings, agent status, errors) | none | **missing** |
| §8.2 Call history + transcript + audio + result | backend `GET /calls`, `GET /calls/{id}` (transcripts) exist; **no frontend page**; no audio (no voice) | **partial** |
| §8.3 Booking management | backend list/create only; no manage UI | **partial** (Standard) |
| §8.4 KB management (no-code CRUD) | `GET /knowledge`, `POST /knowledge/ingest`; no edit/delete, no UI | **partial** |
| §8.5 Roles (Super Admin/Admin/Operator) + §10.1 admin 2FA | only static `X-API-Key`; no users, roles, or 2FA | **missing** |

## 7. Performance & quality (§9)

| Metric | Target | Status |
|---|---|---|
| Latency 1.5–3s (STT+LLM+TTS) | — | **N/A yet** (no voice pipeline; not measured) |
| KB search <500ms | keyword query, unmeasured | **risky/unverified** |
| 1–2 parallel calls | FastAPI async supports it | **unverified** (no load test) |
| Uz/Ru STT accuracy | ≥90% ru; uz pilot-measured | **blocked/risky** (no STT) |

## 8. Security (§10)

| TZ requirement | Code | Status |
|---|---|---|
| TLS 1.3 everywhere | nginx present, no TLS config | **missing** (deploy) |
| Secrets in env only | `.env.example`, settings from env | **done** |
| Admin login + 2FA | `X-API-Key` only | **missing** |
| Every admin action audited | `AuditLogService` exists; **not invoked from admin endpoints** | **partial** |
| Retention (audio 30–90d, transcripts 90–180d, audit ≥1y) | no retention/export jobs | **missing** |
| Data export + delete on termination (§10.3) | none | **missing** |

## 9. Reminders (§11) — Standard scope

`NotificationService.schedule_reminder` logs only. SMS/Telegram + 24h/2h schedule
are **Standard** (§14.1), not Pilot. Status: **head-start / out-of-Pilot-scope**.

## 10. Tests vs §13.1 Pilot Acceptance

| §13.1 acceptance test | Current automated coverage | Status |
|---|---|---|
| 50 calls ≥80% correct | none (no eval harness, no real KB) | **missing** |
| 10 operator transfers ≤30s | only emergency/medical transfer path tested | **partial** |
| 2 parallel calls | none | **missing** |
| 15 uz + 15 ru conversation (native eval) | none (manual/native, not automatable) | **missing** |
| 50 transcripts+audio in admin | transcripts stored (tested); no admin UI; no audio | **partial** |
| Operator participation | no operator console | **missing** |

Existing suite (24 passing) proves: safety classification (uz/ru), AIService
orchestration, call-session lifecycle + audit, basic booking. It does **not** prove
TZ §13.1 acceptance.

---

## Blocked-on-external (cannot start without)
- **Discovery data (§18)**: clinic info, doctors, services/prices, ≥30 FAQ,
  operators, medical-safety policy doc → blocks real KB, doctor/booking scenarios,
  and any §13.1 call test.
- **Provider credentials**: SIP/Twilio, Whisper, TTS, (Standard) Calendar/SMS/Telegram → blocks voice pilot.

## Highest risks (TZ §17 + observed)
1. **Medical safety completeness (Kritik):** keyword guard is incomplete and
   bypassable; missing data-disclosure & negative-talk rules; no injection defense test.
2. **Uz STT/TTS quality (O'rta):** unmeasurable until a voice provider is wired.
3. **Latency budget (1.5–3s):** unproven; full voice chain not built.
4. **No roles/2FA/audit-on-admin:** §10 security not met.
