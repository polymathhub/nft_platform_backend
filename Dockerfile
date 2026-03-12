FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install Python dependencies first (for Docker cache)
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt


# Copy the entire application code (including entrypoint script)
COPY . .

# Set entrypoint script permissions
RUN chmod +x /app/entrypoint.sh && \
    ln -s /app/entrypoint.sh /entrypoint.sh

# Create non-root user and set ownership
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

USER appuser

# Railway sets PORT env var dynamically, default to 8000 for local development
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:$PORT/health', timeout=5).read()" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
