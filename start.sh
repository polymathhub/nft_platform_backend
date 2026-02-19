#!/usr/bin/env bash
# Startup helper for Linux/macOS with uvicorn
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
  echo "Starting in production mode on :$PORT with $WORKERS workers"
  exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers "$WORKERS"
else
  echo "Starting in development mode on :$PORT (auto-reload enabled)"
  exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --reload \
    --log-level debug
fi
