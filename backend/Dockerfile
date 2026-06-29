# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------- #
# Stage 1: build a self-contained virtualenv with all Python dependencies.
# ---------------------------------------------------------------------------- #
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build deps needed to compile psycopg2 (libpq) and other C extensions.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create an isolated virtualenv we can copy into the runtime image.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt


# ---------------------------------------------------------------------------- #
# Stage 2: lean runtime image.
# ---------------------------------------------------------------------------- #
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_DIR=/app

# Only the runtime shared library for psycopg2 is needed here (not the -dev one).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy the prebuilt virtualenv from the builder stage.
COPY --from=builder /opt/venv /opt/venv

WORKDIR ${APP_DIR}

# Copy application code (the .dockerignore keeps out venv/, static/, media/, .env).
COPY . .

RUN chmod +x docker-entrypoint.sh \
    # Run as a non-root user for safety.
    && adduser --disabled-password --gecos "" appuser \
    && mkdir -p ${APP_DIR}/static ${APP_DIR}/media \
    && chown -R appuser:appuser ${APP_DIR}
USER appuser

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
