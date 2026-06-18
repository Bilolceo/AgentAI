# Pilot MVP — Implementation Plan (TZ v2.1 aligned)

Grounded in `docs/TZ_AI_CallCenter_v2.1.md`. See companion docs:
`docs/tz-gap-analysis.md` (what matches the TZ) and
`docs/next-implementation-roadmap.md` (ordered path to acceptance).

**Scope clarification (from the TZ):**
- TZ **Pilot MVP** (§12.2) and **Pilot Acceptance** (§13.1) are a **voice** pilot
  (inbound calls, STT/TTS, audio, 50 live calls).
- CLAUDE.md's **text simulation** is a self-imposed pre-step (Track A in the
  roadmap) — valid, but **not** what §13.1 tests.
- Per §14.1, **RAG/pgvector, Google Calendar/CRM booking, SMS/Telegram reminders
  are Standard package — NOT Pilot.** Keep them out of Pilot scope.

Status: **done · partial · missing · risky · blocked** (only "done" when code _and_
a test prove it — see `tz-gap-analysis.md`).

---

## Phase 1 — Backend foundation  ✅ done
Files: `backend/app/main.py`, `core/{config,db,redis,logging,security}.py`,
`api/deps.py`, `api/v1/{router,health}.py`, `pyproject.toml`, `Dockerfile`.
Acceptance: `GET /health` ok, `/ready` checks DB, `import app.main` ok (15 routes),
secrets via env only (§10.1). **Proof:** app imports; health route present.

## Phase 2 — Database models  ✅ done
Files: `models/{customer,call,transcript,booking,knowledge,audit_log}.py`,
`alembic/` + `versions/0001_initial.py`.
Acceptance: `alembic upgrade head` creates tables + `vector` ext.
**Gap vs TZ:** no doctor/schedule, services/prices, callback-task models (§4.3/§4.6) — **missing**.

## Phase 3 — Call simulation  ✅ done (text) · greeting **missing**
Files: `services/call/session.py`, `schemas/simulation.py`, `api/v1/simulation.py`.
Acceptance: start/message/end; transcripts persisted; uz/ru detected.
**Proof:** `test_call_session` (lifecycle, language, audit). **Gap:** AI greeting on
call start (§6.2) **missing**; voice intake **blocked** (Track B).

## Phase 4 — AI response service  ✅ done · Claude live-validation **partial**
Files: `services/ai/{provider,service,prompts}.py`.
Acceptance: safety→RAG→provider; Mock default; Claude when key set.
**Proof:** `test_ai_service`. **Gap:** no live-KB Claude validation; no confidence
signal for §4.6 low-confidence transfer — **partial**.

## Phase 5 — Medical safety guardrails  🟡 partial · **risky (Kritik)**
Files: `services/safety/guard.py`.
Done: diagnosis/medicine/dosage/treatment transfer + verbatim 103 emergency (uz/ru).
**Proof:** `test_safety` (15). 
**Missing (TZ §5.1):** patient-data-disclosure rule; negative-talk-about-clinics
rule; LLM-side post-generation re-check; injection/paraphrase-bypass tests.
**Risky:** keyword-only guard is bypassable — TZ rates this **Kritik (§17)**.

## Phase 6 — Knowledge base  🟡 partial (engine done, content/CRUD missing)
Files: `services/rag/{service,ingest}.py`, `api/v1/knowledge.py`.
Done: keyword search + ingest (**correct for Pilot — RAG is Standard, §14.1**).
**Proof:** `test_ai_service` (KB answer via stub). 
**Missing:** structured KB (clinic info, services/prices, doctors, FAQ, prep — §8.4);
no-code admin **CRUD** (edit/delete); real seeded content (**blocked on Discovery §18**);
a real `test_rag.py`.

## Phase 7 — Booking  🟢 head-start (Standard scope, not Pilot)
Files: `services/booking/service.py`, `schemas/booking.py`, `api/v1/bookings.py`.
Done: basic `Booking.create` + admin list. **Proof:** `test_booking`.
**Per TZ:** conversational booking, slot proposal, confirm, **Google Calendar/CRM**,
modify/cancel (§4.4/§4.5) are **Standard** — **missing but out of Pilot scope**.

## Phase 8 — Admin dashboard  🟡 partial → **missing** for Pilot acceptance
Files: `frontend/` scaffold + `SimulationChat`; backend `api/v1/calls.py`.
Done: simulation chat; `GET /calls`, `GET /calls/{id}` (transcripts).
**Missing (Pilot-relevant):** `/calls` history UI + transcript view (§8.2 / §13.1
"transcripts visible/downloadable"); main metrics (§8.1); KB CRUD UI (§8.4);
**roles Super Admin/Admin/Operator + admin 2FA (§8.5/§10.1)** — only `X-API-Key` today.

## Phase 9 — Tests  🟡 partial
Files: `tests/{conftest,test_safety,test_ai_service,test_call_session,test_booking}.py`.
Done: **24 passing** (safety, orchestration, lifecycle, booking).
**Missing:** all 8 transfer-trigger cases (§4.6); data-disclosure/negative-talk
safety; `test_rag.py`; FastAPI endpoint tests (invalid input → 4xx); the §13.1
acceptance set (50-call eval, parallel, native uz/ru) — partly **un-automatable**.

## Phase 10 — Docker / deploy  🟡 partial
Files: `infra/docker-compose.yml`, `nginx/nginx.conf`, `scripts/*`, `workers/*`.
Done: compose (pg+pgvector, redis, backend, worker, frontend, nginx), migrate/seed scripts.
**Missing:** end-to-end Docker run not yet executed here; **TLS 1.3** (§10.1);
retention + export/delete jobs (§10.2/§10.3); **CI** (`pytest` on push).

---

## What is genuinely "done" (code + test proven)
Backend foundation, schema+migration, text call lifecycle, AIService orchestration,
core safety classification (5 categories + emergency, uz/ru), basic booking. 24 tests pass.

## What the TZ Pilot still needs (summary)
Safety completeness (§5.1 missing rules) · all §4.6 transfer triggers · greeting ·
real KB content + CRUD · admin transcript/metrics UI · roles/2FA · then the **voice
layer** (telephony/STT/TTS/audio) for §13.1 — **blocked** on Discovery (§18) + provider creds.
