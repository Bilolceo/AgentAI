# AI Voice Call-Center Agent (Clinics)

AI receptionist for clinics: answers calls, gives clinic info, books appointments,
**transfers risky/complex cases to a human operator**, stores transcripts, and
provides an admin dashboard. Uzbek + Russian.

> **Pilot MVP first.** The current build is a **text-based call simulation** with
> safety guardrails — no real telephony yet. Twilio/SIP/STT/TTS are added only
> after the simulation works (see `docs/architecture.md`).

## Medical safety (mandatory)
The AI never diagnoses, names diseases, recommends medicine/dosage, or creates
treatment plans. Urgent symptoms → verbatim **103** emergency guidance + transfer.
Medical-advice requests → operator transfer. Enforced by `SafetyGuardService`
**before** the AI provider, and covered by mandatory tests.

## Architecture (services)
`AIService` · `SafetyGuardService` · `RAGService` · `CallSessionService` ·
`BookingService` · `OperatorTransferService` · `NotificationService` ·
`AuditLogService`. No business logic in route handlers. See `docs/architecture.md`.

## Stack
FastAPI · PostgreSQL + pgvector · SQLAlchemy 2.0 · Alembic · Pydantic v2 · Redis ·
Celery · pytest. Frontend: Next.js + TypeScript + Tailwind. AI: provider interface
(`MockAIProvider` now, `ClaudeAIProvider` later). Infra: Docker Compose.

## Run (Docker)
```bash
cp .env.example .env
cd infra
docker compose up -d --build
docker compose exec backend alembic upgrade head
curl http://localhost:8000/api/v1/health          # {"status":"ok"}
bash scripts/seed.sh                               # optional: seed KB
```
Admin UI: http://localhost:3000 · Simulation chat: http://localhost:3000/simulation

## Tests
```bash
cd backend
pip install -e ".[dev]"
pytest                       # full suite
pytest app/tests/test_safety.py   # mandatory medical-safety tests (no DB)
ruff check .                 # lint
python -m app.eval.run --suite smoke        # 20-scenario mock eval
python -m app.eval.run --suite acceptance   # TZ 50-call mock eval
```

## CI
GitHub Actions runs on every push/PR in mock mode (no secrets, no paid
providers): backend pytest, ruff lint, smoke eval, frontend typecheck + build,
and `docker compose config` validation. See `docs/ci.md`.

## Try the simulation (no telephony)
```bash
CID=$(curl -s -X POST localhost:8000/api/v1/simulation/calls \
  -H 'Content-Type: application/json' -d '{"from_number":"+998901112233"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["call_id"])')
curl -s -X POST localhost:8000/api/v1/simulation/calls/$CID/message \
  -H 'Content-Type: application/json' -d '{"text":"Nafas ololmayapman"}'
```

Voice layer (mock STT/TTS bridge, NOT telephony — see `docs/voice-layer.md`):
```bash
curl -s -X POST localhost:8000/api/v1/voice/simulate \
  -H 'Content-Type: application/json' -d '{"text_override":"Klinika manzili qayerda?"}'
```

## Streaming voice (opt-in, mock-first → real Deepgram)
Twilio Media Streams + streaming STT/TTS/barge-in/latency are layered behind flags,
all OFF by default. Real Deepgram STT/TTS are opt-in. Before any controlled real
call, run the offline preflight
(`cd backend && python -m app.scripts.voice_smoke_preflight`) and/or check
`GET /api/v1/admin/voice-provider-readiness`, then follow the execution runbook in
`docs/live-call-smoke-execution.md` (scenarios in `docs/live-voice-smoke-test.md`).
Docs: `docs/twilio-media-streams.md`, `docs/streaming-stt.md`,
`docs/streaming-tts-playback.md`, `docs/deepgram-streaming-stt.md`,
`docs/deepgram-streaming-tts.md`, `docs/barge-in.md`,
`docs/streaming-latency-metrics.md`.

## Layout
- `backend/` — FastAPI app, services, workers, Alembic migrations, tests
- `frontend/` — Next.js admin dashboard + simulation chat
- `infra/` — docker-compose, nginx, scripts
- `docs/` — architecture, API, call-flows (+ place `TZ_AI_CallCenter_v2.1.docx` here)
