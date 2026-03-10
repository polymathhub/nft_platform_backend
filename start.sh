#!/usr/bin/env bash
# Startup script for NFT Platform Backend
# Handles enum type initialization, Alembic migrations, and FastAPI server startup
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/.venv/bin/activate"

# Activate virtual environment if it exists
if [ -f "$VENV_PATH" ]; then
    echo "Activating virtual environment..."
    # shellcheck disable=SC1091
    source "$VENV_PATH"
else
    echo "Virtual environment not found at $VENV_PATH"
    echo "Please create one with: python -m venv .venv"
    exit 1
fi

# Run the startup script with enum type initialization and migrations
echo "Running startup script with database initialization..."
exec python "$SCRIPT_DIR/startup.py"
