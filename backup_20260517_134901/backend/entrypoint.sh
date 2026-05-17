#!/bin/sh
set -e

echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Starting server..."
exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers ${WORKERS:-2} \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 10 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info}
