#!/bin/sh
set -eu

INTERVAL_SECONDS="${BACKUP_INTERVAL_SECONDS:-86400}"

echo "Database backup scheduler started (every ${INTERVAL_SECONDS}s)"

while true; do
  /scripts/run-backup.sh || echo "Backup failed at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  sleep "${INTERVAL_SECONDS}"
done
