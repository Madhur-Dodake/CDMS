#!/usr/bin/env bash
# ==============================================================================
# CDMS - Nightly PostgreSQL Automated Backup Script
# Usage: ./scripts/backup_db.sh
# Can be run directly or scheduled via cron (e.g. 0 2 * * * /path/to/backup_db.sh)
# ==============================================================================

set -euo pipefail

# 1. Configuration & Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
BACKUP_FILE="${BACKUP_DIR}/cdms_backup_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=7

# Load .env if present
if [ -f "${PROJECT_ROOT}/backend/.env" ]; then
    # shellcheck disable=SC1091
    export $(grep -v '^#' "${PROJECT_ROOT}/backend/.env" | xargs -d '\n')
fi

# Fallback credentials
DB_HOST="${POSTGRES_SERVER:-127.0.0.1}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-cdms_user}"
DB_NAME="${POSTGRES_DB:-cdms_db}"
export PGPASSWORD="${POSTGRES_PASSWORD:-cdms_password}"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting CDMS database backup for ${DB_NAME} on ${DB_HOST}:${DB_PORT}..."

# 2. Execute pg_dump with compression
if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip > "${BACKUP_FILE}"; then
    FILE_SIZE="$(du -h "${BACKUP_FILE}" | cut -f1)"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: Database backup created at ${BACKUP_FILE} (${FILE_SIZE})"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: pg_dump failed!" >&2
    rm -f "${BACKUP_FILE}"
    exit 1
fi

# 3. Retention policy: prune backups older than RETENTION_DAYS
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pruning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "cdms_backup_*.sql.gz" -mtime +"${RETENTION_DAYS}" -exec rm -f {} +
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup cycle completed successfully."
