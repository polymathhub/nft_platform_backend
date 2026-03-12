#!/bin/sh
set -e

# Railway deployment support: use PORT env var if set, default to 8000
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}
HOST=${HOST:-0.0.0.0}

echo "Starting NFT Platform Backend"
echo "  PORT: $PORT"
echo "  WORKERS: $WORKERS"
echo "  HOST: $HOST"

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head

# Start FastAPI app with configurable host and port
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host "$HOST" --port "$PORT" --workers "$WORKERS"
