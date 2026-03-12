#!/bin/sh
set -e

# Run Alembic migrations
alembic upgrade head

# Start FastAPI app
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
