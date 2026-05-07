FROM python:3.11-slim

# System dependencies for WeasyPrint (pango, cairo) + curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[standard]" 2>/dev/null || pip install --no-cache-dir \
    fastapi uvicorn[standard] pydantic pydantic-settings sqlalchemy asyncpg alembic \
    celery redis boto3 anthropic weasyprint jinja2 python-multipart httpx \
    python-jose[cryptography] passlib[bcrypt] sentry-sdk[fastapi] gunicorn slowapi numpy pandas

COPY . .

# Non-root user for security
RUN addgroup --gid 1001 appgroup && \
    adduser --uid 1001 --gid 1001 --no-create-home --disabled-password appuser && \
    chown -R appuser:appgroup /app && \
    mkdir -p /tmp/loglens_uploads && \
    chown -R appuser:appgroup /tmp/loglens_uploads

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1