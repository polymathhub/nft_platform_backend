#!/bin/sh
# =============================================================================
# ROBUST STARTUP SCRIPT - NFT Platform Backend
# 
# Strategy:
#   1. Syntax check (FAIL if invalid code)
#   2. Start app FAST (no blocking operations)
#   3. Migrations run in background via app lifespan events
#   4. App boots in seconds, Railway marks healthy immediately
# =============================================================================

set +e  # Don't fail on first error - we handle errors explicitly

# Railway deployment support: use PORT env var if set, default to 8000
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}
HOST=${HOST:-0.0.0.0}
AUTO_MIGRATE=${AUTO_MIGRATE:-true}

echo "========================================="
echo "  NFT Platform Backend - Production Start"
echo "========================================="
echo "PORT: $PORT"
echo "WORKERS: $WORKERS"
echo "HOST: $HOST"
echo "AUTO_MIGRATE: $AUTO_MIGRATE"
echo "========================================="

# PHASE 1: Pre-flight syntax check (MUST PASS)
echo ""
echo "[1/2] Pre-flight Python syntax check..."
python3 scripts/check_syntax.py
SYNTAX_RESULT=$?
if [ $SYNTAX_RESULT -ne 0 ]; then
    echo "❌ FAILED: Syntax errors detected."
    echo "Container startup aborted."
    exit 1
fi
echo "✅ All Python files have valid syntax"

# PHASE 2: START APP (FAST, non-blocking)
# NOTE: Migrations will run via app lifespan events in async background
echo ""
echo "[2/2] Starting FastAPI application..."
echo "➡️  App will be ready at: http://$HOST:$PORT"
echo "➡️  Health check: http://$HOST:$PORT/health"
echo "➡️  Migrations running in background (if enabled)"
echo ""

# Start uvicorn with proper signal handling
exec uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --loop uvloop \
    --timeout-keep-alive 65
