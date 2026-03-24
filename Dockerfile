FROM python:3.11-slim

LABEL maintainer="NFT Platform Team"
LABEL version="1.0"
LABEL description="Production-ready FastAPI backend for NFT Platform"

# System dependencies (minimal for production)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install Python dependencies first (for Docker layer caching)
# This layer only rebuilds if requirements.txt changes
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code AFTER dependencies
# This is cheaper to rebuild than the pip layer
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY entrypoint.sh .
COPY scripts ./scripts

# Explicitly ensure static files are properly copied and accessible
RUN chmod -R 755 /app/app/static 2>/dev/null || true && \
    chmod -R 644 /app/app/static/webapp/*.html 2>/dev/null || true && \
    chmod -R 644 /app/app/static/webapp/css/* 2>/dev/null || true && \
    chmod -R 644 /app/app/static/webapp/js/* 2>/dev/null || true

# Set entrypoint script permissions
RUN chmod +x /app/entrypoint.sh && \
    chmod +x /app/scripts/check_syntax.py

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

USER appuser

# Dynamic PORT from environment (Railway, Heroku, etc.)
ENV PORT=8000
ENV WORKERS=4

EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
