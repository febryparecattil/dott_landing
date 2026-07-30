"""SQLite storage for form submissions, rate limiting and the admin audit log.

A single file database is enough here: submissions arrive a handful of times a
day and only ever from this one box. WAL mode plus a busy timeout is what makes
it safe across gunicorn's three workers.
"""
import json
import os
import sqlite3
import time
from datetime import datetime, timezone

import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS waitlist (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    email       TEXT    NOT NULL,
    phone       TEXT,
    source_ip   TEXT
);

CREATE TABLE IF NOT EXISTS registrations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at    TEXT    NOT NULL,
    profession    TEXT,
    name          TEXT    NOT NULL,
    mobile        TEXT    NOT NULL,
    email         TEXT    NOT NULL,
    whatsapp      INTEGER,
    city          TEXT,
    state         TEXT,
    license       TEXT,
    qualification TEXT,
    experience    TEXT,
    extra         TEXT,
    source_ip     TEXT
);

-- Rate limiting. Kept in the database rather than process memory so the
-- three gunicorn workers share one view of who has been knocking.
CREATE TABLE IF NOT EXISTS events (
    bucket TEXT    NOT NULL,
    ts     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_bucket_ts ON events (bucket, ts);

CREATE TABLE IF NOT EXISTS admin_audit (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ts     TEXT NOT NULL,
    ip     TEXT,
    event  TEXT NOT NULL,
    detail TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON admin_audit (ts);
"""

# Registration columns stored in their own field; everything else on the
# payload is kept as JSON in `extra` so new form fields never need a migration.
REGISTRATION_COLUMNS = (
    "profession",
    "name",
    "mobile",
    "email",
    "whatsapp",
    "city",
    "state",
    "license",
    "qualification",
    "experience",
)


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect():
    """Open a connection, creating the database with tight permissions."""
    path = settings.DB_PATH
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, mode=0o700, exist_ok=True)

    is_new = not os.path.exists(path)
    conn = sqlite3.connect(path, timeout=settings.DB_TIMEOUT)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=%d" % int(settings.DB_TIMEOUT * 1000))
    conn.execute("PRAGMA synchronous=FULL")
    if is_new:
        # Submissions are personal data - never world or group readable.
        os.chmod(path, 0o600)
    return conn


def init():
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def insert_waitlist(data, source_ip=None):
    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO waitlist (created_at, name, email, phone, source_ip)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                utcnow(),
                str(data.get("name", "")).strip(),
                str(data.get("email", "")).strip(),
                str(data.get("phone", "")).strip(),
                source_ip,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def insert_registration(data, source_ip=None):
    known = {}
    for column in REGISTRATION_COLUMNS:
        value = data.get(column)
        if column == "whatsapp":
            known[column] = 1 if value else 0
        else:
            known[column] = str(value).strip() if value is not None else ""

    extra = {}
    for key, value in data.items():
        if key in REGISTRATION_COLUMNS:
            continue
        if value in (None, "", [], {}):
            continue
        extra[key] = value

    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO registrations (created_at, profession, name, mobile,"
            " email, whatsapp, city, state, license, qualification, experience,"
            " extra, source_ip) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                utcnow(),
                known["profession"],
                known["name"],
                known["mobile"],
                known["email"],
                known["whatsapp"],
                known["city"],
                known["state"],
                known["license"],
                known["qualification"],
                known["experience"],
                json.dumps(extra, ensure_ascii=False) if extra else None,
                source_ip,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def count(table):
    if table not in ("waitlist", "registrations"):
        raise ValueError("unknown table")
    conn = connect()
    try:
        return conn.execute("SELECT COUNT(*) AS n FROM %s" % table).fetchone()["n"]
    finally:
        conn.close()


def recent(table, limit=50, offset=0):
    if table not in ("waitlist", "registrations"):
        raise ValueError("unknown table")
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM %s ORDER BY id DESC LIMIT ? OFFSET ?" % table,
            (int(limit), int(offset)),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def all_rows(table):
    if table not in ("waitlist", "registrations"):
        raise ValueError("unknown table")
    conn = connect()
    try:
        rows = conn.execute("SELECT * FROM %s ORDER BY id" % table).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# --- rate limiting -------------------------------------------------------

def hit(bucket, window_seconds):
    """Record an event and return how many happened in the trailing window."""
    now = int(time.time())
    conn = connect()
    try:
        conn.execute("INSERT INTO events (bucket, ts) VALUES (?, ?)", (bucket, now))
        # Opportunistic prune so the table cannot grow without bound.
        conn.execute("DELETE FROM events WHERE ts < ?", (now - 86400,))
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM events WHERE bucket = ? AND ts > ?",
            (bucket, now - int(window_seconds)),
        ).fetchone()
        conn.commit()
        return row["n"]
    finally:
        conn.close()


def count_in_window(bucket, window_seconds):
    now = int(time.time())
    conn = connect()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM events WHERE bucket = ? AND ts > ?",
            (bucket, now - int(window_seconds)),
        ).fetchone()
        return row["n"]
    finally:
        conn.close()


def clear_bucket(bucket):
    conn = connect()
    try:
        conn.execute("DELETE FROM events WHERE bucket = ?", (bucket,))
        conn.commit()
    finally:
        conn.close()


# --- audit ---------------------------------------------------------------

def audit(event, ip=None, detail=None):
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO admin_audit (ts, ip, event, detail) VALUES (?, ?, ?, ?)",
            (utcnow(), ip, event, detail),
        )
        conn.commit()
    finally:
        conn.close()


def recent_audit(limit=25):
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM admin_audit ORDER BY id DESC LIMIT ?", (int(limit),)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
