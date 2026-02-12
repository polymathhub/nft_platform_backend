#!/usr/bin/env bash
# Simple startup helper for Linux/macOS
set -euo pipefail

# Load .env if present
if [ -f .env ]; then
  # shellcheck disable=SC1091
  export $(grep -v '^#' .env | xargs)
fi

PORT=${PORT:-8000}
ENV=${ENV:-development}
WORKERS=${WORKERS:-4}

if [ "$ENV" = "production" ]; then
  echo "Starting in production mode on :$PORT"
  exec gunicorn app.main:app -w "$WORKERS" -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:"$PORT"
else
  echo "Starting in development mode on :$PORT (auto-reload)"
  exec uvicorn app.main:app --reload --host 0.0.0.0 --port "$PORT"
fi
