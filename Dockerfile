# =============================================================================
# Stage 1 – builder
# Install all Python dependencies into an isolated prefix so the runtime stage
# receives only the compiled wheels with no build toolchain bloat.
# =============================================================================
FROM python:3.12-slim AS builder

# Prevent Python from writing .pyc files or buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build-time OS dependencies (gcc is needed by some C-extension wheels)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the dependency manifest first to exploit Docker layer caching.
# If requirements.txt does not change, pip install is skipped on rebuilds.
COPY requirements.txt .

# Install all packages into /install so they can be copied cleanly to the
# runtime image without dragging along pip, setuptools, wheel, etc.
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-warn-script-location -r requirements.txt


# =============================================================================
# Stage 2 – runtime
# Minimal image that runs the application as a non-root user.
# =============================================================================
FROM python:3.12-slim AS runtime

# Prevent Python from writing .pyc files or buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Tell Python where to find the packages copied from the builder stage
    PYTHONPATH=/install/lib/python3.12/site-packages \
    # Ensure scripts installed by pip (uvicorn, alembic, etc.) are on PATH
    PATH=/install/bin:$PATH

# Install only the runtime OS libraries required by psycopg2 (libpq) and
# the health-check curl call.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /install

# Create a non-root user and group for the application process
RUN groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy application source code
COPY --chown=appuser:appuser app/ ./app/

# Drop privileges — everything from here on runs as appuser
USER appuser

EXPOSE 8000

# Docker-native health check: hits the /health endpoint every 30 s.
# The container is considered healthy after 2 consecutive successes and
# unhealthy after 3 consecutive failures.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn with production-safe defaults.
# Worker count is intentionally kept at 1 here; scale horizontally via
# replicas in docker-compose or Kubernetes rather than multiple processes
# inside a single container.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
