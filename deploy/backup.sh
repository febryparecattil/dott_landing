#!/bin/bash
# Nightly snapshot of the submissions database.
#
# Uses sqlite3 .backup rather than cp: it takes a consistent copy even while
# the app is mid-write, which a plain file copy in WAL mode does not.
set -euo pipefail

DB_PATH="${DB_PATH:-/var/lib/dott/dott.db}"
BACKUP_DIR="${BACKUP_DIR:-/var/lib/dott/backups}"
KEEP_DAYS="${KEEP_DAYS:-30}"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

if [ ! -f "$DB_PATH" ]; then
  echo "No database at $DB_PATH yet - nothing to back up."
  exit 0
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="$BACKUP_DIR/dott-$STAMP.db"

sqlite3 "$DB_PATH" ".backup '$TARGET'"
gzip -f "$TARGET"
chmod 600 "$TARGET.gz"

find "$BACKUP_DIR" -name 'dott-*.db.gz' -mtime "+$KEEP_DAYS" -delete

echo "Backed up to $TARGET.gz"
echo "NOTE: this stays on the same EBS volume as the database. Ship it"
echo "off-instance (S3) for real durability."
