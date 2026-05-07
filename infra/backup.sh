#!/bin/sh
# Daily PostgreSQL backup to S3
# Run via cron: 0 2 * * * /opt/loglens/infra/backup.sh >> /var/log/loglens-backup.log 2>&1

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="loglens_${TIMESTAMP}.sql.gz"
KEEP_DAYS=30

echo "[backup] Starting: ${TIMESTAMP}"

# Dump + gzip + upload in one pipeline (no temp file needed)
pg_dump \
  --host="${POSTGRES_HOST:-postgres}" \
  --username="${POSTGRES_USER:-loglens}" \
  --no-password \
  "${POSTGRES_DB:-loglens}" \
  | gzip \
  | aws s3 cp - "s3://${S3_BACKUP_BUCKET}/postgres/${FILENAME}" \
      --region "${AWS_REGION:-us-east-1}"

echo "[backup] Uploaded: s3://${S3_BACKUP_BUCKET}/postgres/${FILENAME}"

# Delete backups older than KEEP_DAYS days
CUTOFF=$(date -d "${KEEP_DAYS} days ago" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || \
         date -v -${KEEP_DAYS}d +%Y-%m-%dT%H:%M:%SZ)

aws s3 ls "s3://${S3_BACKUP_BUCKET}/postgres/" \
  | awk '{print $4}' \
  | while read -r f; do
      FILE_DATE=$(echo "$f" | grep -oP '\d{8}' | head -1)
      FILE_TS=$(date -d "${FILE_DATE}" +%s 2>/dev/null || date -j -f "%Y%m%d" "${FILE_DATE}" +%s)
      CUTOFF_TS=$(date -d "${CUTOFF}" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "${CUTOFF}" +%s)
      if [ "${FILE_TS}" -lt "${CUTOFF_TS}" ]; then
        aws s3 rm "s3://${S3_BACKUP_BUCKET}/postgres/${f}" --region "${AWS_REGION:-us-east-1}"
        echo "[backup] Deleted old backup: ${f}"
      fi
    done

echo "[backup] Done: ${TIMESTAMP}"