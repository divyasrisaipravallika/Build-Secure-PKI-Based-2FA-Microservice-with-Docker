#!/bin/sh
set -e

# Ensure data directories exist (mounted volumes)
mkdir -p /data /cron
chmod 700 /data || true
chmod 755 /cron || true

# Ensure cron file in /etc/cron.d has correct perms and newline
if [ -f /etc/cron.d/pki-cron ]; then
  chmod 0644 /etc/cron.d/pki-cron
  # ensure crontab is installed (best-effort)
  crontab /etc/cron.d/pki-cron || true
fi

# Start cron daemon (background)
# Try service cron start; if not available, run cron as daemon
if command -v service >/dev/null 2>&1; then
  service cron start || true
else
  # run cron in background
  cron || true
fi

# Start the FastAPI server with uvicorn
# Use environment var to set host/port if provided
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8080}

exec uvicorn main:app --host "$HOST" --port "$PORT"
