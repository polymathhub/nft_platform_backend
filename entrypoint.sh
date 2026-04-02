#!/bin/bash
set -e

# ---------------------------------------------------------------------------
# Entrypoint for the NFT Platform FastAPI backend
#
# Responsibilities:
#   1. Run Alembic database migrations (alembic upgrade head)
#   2. Start the Uvicorn server using PORT and WORKERS env vars
#
# Environment variables (with defaults):
#   PORT    – TCP port Uvicorn listens on  (default: 8000)
#   WORKERS – Number of Uvicorn workers    (default: 4)
# ---------------------------------------------------------------------------

PORT="${PORT:-8000}"
WORKERS="${WORKERS:-4}"

echo "=== NFT Platform Backend ==="
echo "Port:    ${PORT}"
echo "Workers: ${WORKERS}"
echo ""

# ---------------------------------------------------------------------------
# 1. Database migrations
# ---------------------------------------------------------------------------
echo ">>> Running database migrations..."
alembic upgrade head
echo ">>> Migrations complete."
echo ""

# ---------------------------------------------------------------------------
# 2. Start Uvicorn
# ---------------------------------------------------------------------------
echo ">>> Starting Uvicorn on 0.0.0.0:${PORT} with ${WORKERS} worker(s)..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers "${WORKERS}"
