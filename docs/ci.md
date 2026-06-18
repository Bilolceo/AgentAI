# CI (text-pilot MVP)

GitHub Actions workflow: `.github/workflows/ci.yml`. Runs on every push and pull
request. Mock mode only - no real Claude/Twilio/STT/TTS, no paid providers, no
secrets. `AI_PROVIDER=mock` is set at the workflow level.

## Jobs
- backend-tests - Python 3.12, `pip install -e ".[dev]"`, `pytest` (in-memory
  SQLite, mock provider; no Postgres service or migrations needed for tests).
- backend-lint - `ruff check .`.
- eval-smoke - `python -m app.eval.run --suite smoke`; the runner exits non-zero
  if any scenario fails, so CI gates on it.
- frontend-checks - Node 20, `npm ci`, `npx tsc --noEmit`, `npm run build`.
- docker-config - `cp .env.example .env` then
  `docker compose -f infra/docker-compose.yml config` (parse/validate only; no
  image build, no Docker daemon required).

Pip and npm caches are keyed on `backend/pyproject.toml` and
`frontend/package-lock.json`.

## Run the same checks locally
Backend tests:

    cd backend && pip install -e ".[dev]" && pytest -q

Backend lint:

    cd backend && ruff check .

Frontend typecheck:

    cd frontend && npm ci && npx tsc --noEmit

Smoke eval (mock):

    cd backend && python -m app.eval.run --suite smoke

Acceptance eval (mock, 50 calls):

    cd backend && python -m app.eval.run --suite acceptance

Multi-turn eval (mock; NOT run in CI - slower, per-scenario in-memory DB):

    cd backend && python -m app.eval.run --suite multiturn

Docker compose config validation:

    cp .env.example .env
    docker compose -f infra/docker-compose.yml config

## What CI does NOT cover yet
- No real Claude eval (live API is optional and run manually; see
  docs/acceptance-eval.md and docs/live-claude-provider.md).
- No multi-turn eval (run locally with `--suite multiturn`; see
  docs/multiturn-eval.md). It is slower than smoke and is intentionally not in CI.
- No Docker image build or runtime/integration test against a live backend
  container (only `docker compose config` is validated).
- No Postgres-backed migration test (`alembic upgrade head` against a real DB);
  tests use in-memory SQLite.
- No telephony/STT/TTS/SIP (out of scope for the text pilot).
- No end-to-end frontend test (only typecheck + build), no coverage gate, no
  security/dependency scanning.
