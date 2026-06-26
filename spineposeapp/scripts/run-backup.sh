#!/bin/bash
set -euo pipefail

TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
BACKUP_FILE="/tmp/spinepose_${TIMESTAMP}.sql.gz"
BACKUP_BUCKET="${MINIO_BACKUP_BUCKET:-backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting database backup"

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h postgres -U spinepose -d spinepose | gzip > "$BACKUP_FILE"

mc alias set spinepose "http://${MINIO_ENDPOINT}" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc mb --ignore-existing "spinepose/${BACKUP_BUCKET}"
mc cp "$BACKUP_FILE" "spinepose/${BACKUP_BUCKET}/spinepose_${TIMESTAMP}.sql.gz"

mc find "spinepose/${BACKUP_BUCKET}" --name "spinepose_*.sql.gz" --older-than "${RETENTION_DAYS}d" --exec "mc rm {}"

rm -f "$BACKUP_FILE"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Backup uploaded: spinepose_${TIMESTAMP}.sql.gz"
