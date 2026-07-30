#!/bin/bash
# Nightly snapshot of the submissions database.
#
# Uses the sqlite3 backup API via Python rather than the sqlite3 CLI (which is
# not installed on the server) and rather than cp: the backup API takes a
# consistent copy even while the app is mid-write, which a plain file copy in
# WAL mode does not.
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ubuntu/dott_landing}"
DB_PATH="${DB_PATH:-/var/lib/dott/dott.db}"
BACKUP_DIR="${BACKUP_DIR:-/var/lib/dott/backups}"
KEEP_DAYS="${KEEP_DAYS:-30}"
PYTHON="${PYTHON:-$APP_DIR/venv/bin/python}"

if [ ! -f "$DB_PATH" ]; then
  echo "No database at $DB_PATH yet - nothing to back up."
  exit 0
fi

if [ ! -x "$PYTHON" ]; then
  echo "ERROR: no interpreter at $PYTHON" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="$BACKUP_DIR/dott-$STAMP.db"

"$PYTHON" - "$DB_PATH" "$TARGET" <<'PY'
import sqlite3
import sys

source_path, target_path = sys.argv[1], sys.argv[2]
source = sqlite3.connect("file:%s?mode=ro" % source_path, uri=True)
target = sqlite3.connect(target_path)
with target:
    source.backup(target)
target.close()
source.close()

# Fail loudly rather than leaving a silently empty backup.
check = sqlite3.connect(target_path)
tables = {
    row[0]
    for row in check.execute("SELECT name FROM sqlite_master WHERE type='table'")
}
check.close()
if not {"waitlist", "registrations"} <= tables:
    sys.exit("backup is missing expected tables: %s" % sorted(tables))
print("  verified tables: %s" % ", ".join(sorted(tables)))
PY

gzip -f "$TARGET"
chmod 600 "$TARGET.gz"

find "$BACKUP_DIR" -name 'dott-*.db.gz' -mtime "+$KEEP_DAYS" -delete

echo "Backed up to $TARGET.gz ($(du -h "$TARGET.gz" | cut -f1))"
echo "NOTE: this stays on the same EBS volume as the database. Ship it"
echo "off-instance (S3) for real durability."
