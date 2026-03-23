#!/bin/bash
# =============================================================================
# PRODUCTION STARTUP SCRIPT - NFT Platform Backend
# 
# Optimized for Railway deployment with:
# - Fast startup (< 30 seconds to health check)
# - Non-blocking migrations and Telegram setup
# - Graceful error handling and recovery
# - Proper signal handling for orchestrators
#
# Environment Variables:
#   PORT (default: 8000)
#   WORKERS (default: 4)
#   HOST (default: 0.0.0.0)
#   AUTO_MIGRATE (default: true)
#   LOG_LEVEL (default: info)
# =============================================================================

set -e
trap 'echo "ERROR: Startup failed"; exit 1' ERR

# Load environment
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}
HOST=${HOST:-0.0.0.0}
AUTO_MIGRATE=${AUTO_MIGRATE:-true}
LOG_LEVEL=${LOG_LEVEL:-info}

echo "======================================================================"
echo "  🚀 NFT Platform Backend - Production Startup"
echo "======================================================================"
echo "  Environment: production"
echo "  HOST: $HOST | PORT: $PORT | WORKERS: $WORKERS"
echo "  AUTO_MIGRATE: $AUTO_MIGRATE | LOG_LEVEL: $LOG_LEVEL"
echo "======================================================================"
echo ""

# Pre-startup checks
echo "[Startup] Verifying configuration..."
if [ -z "$DATABASE_URL" ]; then
    echo "⚠ WARNING: DATABASE_URL not set"
    echo "  App will use local SQLite for development"
fi

if [ ! -f "app/main.py" ]; then
    echo "❌ FATAL: app/main.py not found"
    exit 1
fi

echo "[Startup] ✓ Configuration verified"
echo ""
echo "======================================================================"
echo "  Starting FastAPI application..."
echo "======================================================================"
echo "  Health check:  GET http://$HOST:$PORT/health"
echo "  API docs:      http://$HOST:$PORT/docs"
echo "  Migrations:    Running in background (async)"
echo "======================================================================"
echo ""

# Start uvicorn with optimized settings for Railway
exec uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --loop uvloop \
    --timeout-keep-alive 65 \
    --timeout-graceful-shutdown 15 \
    --log-level "$LOG_LEVEL"
