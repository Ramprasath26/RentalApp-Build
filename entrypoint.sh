#!/bin/sh
set -e

# Optional: run migrations before boot (controlled via env var)
if [ "${RUN_MIGRATIONS}" = "true" ]; then
    echo "[entrypoint] Running database migrations..."
    python manage.py migrate --noinput
fi

# Collect static files (required for Django admin CSS in production)
echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "[entrypoint] Starting Gunicorn on 0.0.0.0:${PORT:-8000}..."
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --log-level "${GUNICORN_LOG_LEVEL:-info}" \
    --access-logfile "-" \
    --error-logfile "-"
