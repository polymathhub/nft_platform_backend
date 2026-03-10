# Production-ready Dockerfile for NFT Platform Backend FastAPI
# Fixes: Module import errors, working directory, health checks, async compatibility

FROM python:3.11-slim

# ============================================================================
# BUILD ARGUMENTS & ENVIRONMENT VARIABLES
# ============================================================================

ARG PYTHON_VERSION=3.11
ARG ENVIRONMENT=production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=${ENVIRONMENT} \
    WORKERS=4 \
    WORKER_CLASS=uvicorn.workers.UvicornWorker

# ============================================================================
# SYSTEM DEPENDENCIES (lean image for production)
# ============================================================================

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# WORKING DIRECTORY (critical for correct imports)
# ============================================================================

WORKDIR /app

# ============================================================================
# PYTHON DEPENDENCIES (in correct order for production)
# ============================================================================

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ============================================================================
# APPLICATION CODE
# ============================================================================

# Copy entire application (with proper working directory set above)
COPY . .

# ============================================================================
# PERMISSIONS & VALIDATION
# ============================================================================

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Validate that the app module can be imported
RUN python -c "from app.main import app; print('✓ app.main:app imported successfully')" || \
    (echo "✗ ERROR: Could not import app.main:app" && exit 1)

# ============================================================================
# PORT & HEALTHCHECK (Railway expects this)
# ============================================================================

EXPOSE 8000

# Health check using Python to ensure /health endpoint is accessible
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5).read()" || exit 1

# ============================================================================
# ENTRYPOINT (production with async support and auto-scaling)
# ============================================================================

# Run Alembic migrations first, then start uvicorn
CMD ["sh", "-c", "\
  echo 'Starting NFT Platform Backend...' && \
  echo 'Running database migrations...' && \
  alembic upgrade head && \
  echo 'Starting uvicorn server...' && \
  uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --loop uvloop \
    --http h11 \
    --access-log \
    --log-config /app/app/config/logging.yaml || \
  (echo 'ERROR: Failed to start server'; exit 1)"]
