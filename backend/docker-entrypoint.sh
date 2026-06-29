#!/bin/sh
set -e

# Apply DB migrations and collect static files at boot (idempotent).
# Set RUN_MIGRATIONS=0 to skip migrations (e.g. when running multiple replicas
# and migrations are handled by a separate one-off job).
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "[entrypoint] Running migrations..."
  python manage.py migrate --noinput
fi

if [ "${COLLECT_STATIC:-1}" = "1" ]; then
  echo "[entrypoint] Collecting static files..."
  python manage.py collectstatic --noinput
fi

echo "[entrypoint] Starting server on port ${PORT:-8000}..."
exec gunicorn api_chat_bot.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  -b "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --graceful-timeout 30 \
  --access-logfile - \
  --error-logfile -
