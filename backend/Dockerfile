FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_PROJECT_ENVIRONMENT=/venv

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ── dependencies stage ─────────────────────────────────────────────────────────
FROM base AS deps

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev

# ── production stage ───────────────────────────────────────────────────────────
FROM base AS production

COPY --from=deps /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY . .

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "httptools"]

# ── development stage ──────────────────────────────────────────────────────────
FROM base AS development

COPY --from=deps /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY . .

CMD ["/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── celery worker stage ────────────────────────────────────────────────────────
FROM production AS celery-worker

CMD ["/venv/bin/celery", "-A", "app.workers.celery_app", "worker", "--loglevel=info", "--concurrency=4", "-E"]

# ── celery beat stage ──────────────────────────────────────────────────────────
FROM production AS celery-beat

CMD ["/venv/bin/celery", "-A", "app.workers.celery_app", "beat", "--loglevel=info", "--scheduler", "celery.beat:PersistentScheduler"]
