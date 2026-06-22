#!/bin/sh
set -e
PORT="${PORT:-8000}"
echo "BOOT: starting, PORT=${PORT}"
alembic upgrade head
echo "BOOT: migrations done, launching uvicorn"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --log-level info
