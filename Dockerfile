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

# Copy application code and entrypoint
COPY . .

# Set permissions for entrypoint before switching user
RUN chmod +x /entrypoint.sh

# Create non-root user and set ownership
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5).read()" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
