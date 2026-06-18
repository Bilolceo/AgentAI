# Docker demo: one-command local run (text pilot MVP)

Runs postgres + redis + backend + frontend. Default AI provider is mock, so no
API key is needed. No telephony/STT/TTS.

## 1. Prerequisites
- Docker Engine + Docker Compose v2 (or newer).
- Free local ports: 8000 (backend), 3000 (frontend), 5432 (postgres), 6379 (redis).

## 2. Copy the env file
From the project root:

    cp .env.example .env

Defaults are demo-ready: APP_ENV=development, AI_PROVIDER=mock,
DATABASE_URL points at the postgres service, NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1.
Change JWT_SECRET before any non-local use.

## 3. Start
    cd infra
    docker compose up --build

Backend waits for postgres (healthcheck), runs migrations, then serves the API.
Frontend waits for the backend healthcheck before starting.

## 4. Migrations
Run automatically on backend startup (compose runs `alembic upgrade head` first).
To run them manually:

    docker compose exec backend alembic upgrade head

## 5. Create the first super_admin
Dev/test only (APP_ENV=development|test). It is NOT exposed when APP_ENV is
anything else.

    curl -X POST http://localhost:8000/api/v1/auth/dev-bootstrap-super-admin \
      -H 'Content-Type: application/json' \
      -d '{"email":"admin@clinic.uz","password":"Admin12345","full_name":"Admin"}'

(Password policy: at least 10 chars with a letter and a digit.)

## 6. Login URL
    http://localhost:3000/login

Log in as admin@clinic.uz / Admin12345. Admin pages: /admin (overview, calls,
knowledge base, callbacks, audit logs, users, security/2FA).

## 7. Seed demo knowledge base
One script does bootstrap + login + seed:

    bash infra/scripts/seed.sh

Or manually (super_admin token required):

    TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
      -H 'Content-Type: application/json' \
      -d '{"email":"admin@clinic.uz","password":"Admin12345"}' \
      | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
    curl -X POST http://localhost:8000/api/v1/admin/knowledge/seed -H "Authorization: Bearer $TOKEN"

## 8. Run a text simulation
Use the UI at http://localhost:3000/simulation, or the API:

    CID=$(curl -s -X POST http://localhost:8000/api/v1/simulation/calls \
      -H 'Content-Type: application/json' -d '{"from_number":"+998901112233"}' \
      | python3 -c 'import sys,json;print(json.load(sys.stdin)["call_id"])')

    curl -s -X POST http://localhost:8000/api/v1/simulation/calls/$CID/message \
      -H 'Content-Type: application/json' -d '{"text":"Klinika manzili qayerda?"}'

    curl -s -X POST http://localhost:8000/api/v1/simulation/calls/$CID/message \
      -H 'Content-Type: application/json' -d '{"text":"Nafas ololmayapman"}'   # emergency -> 103

## 9. Run backend tests
Outside Docker (fastest):

    cd backend && pip install -e ".[dev]" && pytest

Inside the container:

    docker compose exec backend pytest

Eval harness (deterministic, mock):

    docker compose exec backend python -m app.eval.run

## 10. Switch to Claude provider mode (optional, real API, billed)
Edit .env:

    AI_PROVIDER=claude
    ANTHROPIC_API_KEY=sk-ant-...
    CLAUDE_MODEL=claude-sonnet-4-6

Recreate the backend (AI_PROVIDER is read at runtime; no image rebuild needed):

    docker compose up -d backend

If AI_PROVIDER=claude and ANTHROPIC_API_KEY is missing, the backend fails fast
with a clear configuration error. See docs/live-claude-provider.md.

## 11. Troubleshooting
- Port already in use: stop the conflicting process or change the published port
  in infra/docker-compose.yml.
- Reset the database (drops all data, re-runs migrations on next up):
    docker compose down -v
- Backend stuck "starting": it waits for postgres healthy; check
    docker compose logs backend
- Frontend calls the wrong API URL: NEXT_PUBLIC_API_BASE is baked at build time.
  After changing it, rebuild the frontend:
    NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1 docker compose build frontend
- 401/403 on admin endpoints: log in first and send the Bearer token; operators
  cannot access manager-only endpoints.
- Stop everything:
    docker compose down
