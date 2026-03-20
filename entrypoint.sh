#!/bin/sh
set -e

# Railway deployment support: use PORT env var if set, default to 8000
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}
HOST=${HOST:-0.0.0.0}

echo "========================================="
echo "  NFT Platform Backend - Production Start"
echo "========================================="
echo "PORT: $PORT"
echo "WORKERS: $WORKERS"
echo "HOST: $HOST"

# PRE-FLIGHT: Check for syntax errors
echo ""
echo "[1/3] Pre-flight syntax check..."
python3 scripts/check_syntax.py
if [ $? -ne 0 ]; then
    echo "❌ FAILED: Syntax errors detected. Container startup aborted."
    exit 1
fi
echo "✅ All Python files valid"

# RUN MIGRATIONS
echo ""
echo "[2/3] Running database migrations..."
alembic upgrade head
if [ $? -ne 0 ]; then
    echo "❌ FAILED: Database migrations failed"
    exit 1
fi
echo "✅ Migrations complete"

# START APP
echo ""
echo "[3/3] Starting FastAPI application..."
echo "Application will be available at http://$HOST:$PORT"
echo "Health check: http://$HOST:$PORT/health"
echo ""
exec uvicorn app.main:app --host "$HOST" --port "$PORT" --workers "$WORKERS" --loop uvloop --timeout-keep-alive 65
