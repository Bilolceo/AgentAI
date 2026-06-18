#!/usr/bin/env bash
set -euo pipefail
# Run DB migrations inside the backend container.
docker compose exec backend alembic upgrade head
