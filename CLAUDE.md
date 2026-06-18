# CLAUDE.md — AI Voice Call-Center Agent (Clinics)

## Project Goal
AI voice receptionist for clinics: answers inbound calls, gives clinic info, books
appointments, transfers risky/complex cases to a human operator, stores
transcripts, and provides an admin dashboard. Uzbek + Russian.

## MVP first (NOT enterprise)
Build the **Pilot MVP** before anything else. Pilot MVP = **text-based call
simulation** with: backend API, clinic knowledge base, AI response service (mock
provider first), safety guardrails, operator-transfer logic, basic booking model,
basic admin dashboard, call logs/transcripts, tests.

> **Do NOT implement real SIP/Twilio/STT/TTS until the text-based simulation works.**
> Provider interface first; mock AI provider for tests; Claude/OpenAI later.

## Critical Medical Safety Rules (mandatory)
The AI agent MUST NOT: diagnose, suggest diseases, recommend medicine/dosage,
create treatment plans, disclose patient data to third parties, speak negatively
about other clinics/doctors, or continue during an emergency.

Emergency response (verbatim):
> "Bu holat shoshilinch tibbiy yordam talab qilishi mumkin. Iltimos, darhol 103
> raqamiga qo'ng'iroq qiling yoki eng yaqin shifoxonaga murojaat qiling."

If the user asks for diagnosis, medicine, dosage, treatment, or reports urgent
symptoms → transfer to operator or give emergency guidance. **Safety tests are
mandatory** and must pass.

## Architecture rules
Clean modular architecture. **No business logic in route handlers.** Services:
- `AIService` — orchestrates provider + RAG + safety
- `SafetyGuardService` — medical safety (pure logic, no external deps → unit-testable)
- `RAGService` — knowledge base retrieval (pgvector)
- `CallSessionService` — call/session lifecycle (text simulation)
- `BookingService` — appointments (DB model now; Google Calendar/CRM later)
- `OperatorTransferService` — escalation decisions
- `NotificationService` — SMS/Telegram reminders (mock/log now)
- `AuditLogService` — append-only audit trail

**Every important action is logged via AuditLogService:** call started, language
detected, AI response generated, safety guard triggered, operator transfer
requested, booking created, reminder scheduled.

## Security
No secrets in code (`.env.example` only). Validate all external inputs. Audit
admin actions. Protect patient data. Never expose raw internal errors to users.

## Stack
Backend: FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic, Pydantic v2, Redis, pytest.
Frontend: Next.js, TypeScript, TailwindCSS, shadcn/ui (if useful).
AI: provider interface → Claude/OpenAI later; RAG via pgvector; mock provider for tests.
Infra: Docker Compose, `.env.example`, CI-ready.

## Workflow
Read existing files → short plan → implement in small steps → add tests → run
tests → summarize changed files. Mandatory test coverage: medical safety,
emergency detection, operator transfer, KB answer, booking creation, call-session
lifecycle, invalid input.

## Language convention
Explain to the project owner in **Uzbek**. Code identifiers in **English**.
Comments English unless business logic needs Uzbek examples.

## Quick commands
```bash
cd infra && docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend pytest
# Safety tests only (no DB needed):
cd backend && pytest app/tests/test_safety.py
```
