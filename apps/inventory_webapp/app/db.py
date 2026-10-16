"""SQLite access + idempotent review-column migration."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from app.config import db_path

BUSY_TIMEOUT_MS = 30_000

REVIEW_COLUMNS = {
    "status": "TEXT NOT NULL DEFAULT 'pending'",
    "amended_qty": "REAL",
    "amended_notes": "TEXT",
    "reviewed_at": "TEXT",
    "reviewed_by": "TEXT",
}


def connect(readonly: bool = False) -> sqlite3.Connection:
    path = db_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Database not found: {path}. Run: make seed-hubby (riser-inventory ingest)"
        )
    if readonly:
        conn = sqlite3.connect(
            f"file:{path}?mode=ro", uri=True, timeout=BUSY_TIMEOUT_MS / 1000.0
        )
    else:
        conn = sqlite3.connect(str(path), timeout=BUSY_TIMEOUT_MS / 1000.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    return conn


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r["name"] for r in rows}


def migrate(conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    c = conn or connect()
    cols = _existing_columns(c, "occurrences")
    for name, decl in REVIEW_COLUMNS.items():
        if name not in cols:
            c.execute(f"ALTER TABLE occurrences ADD COLUMN {name} {decl}")
    # Ensure status backfill
    c.execute(
        "UPDATE occurrences SET status = 'pending' WHERE status IS NULL OR status = ''"
    )
    c.commit()
    if own:
        c.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextmanager
def get_db(readonly: bool = False) -> Iterator[sqlite3.Connection]:
    conn = connect(readonly=readonly)
    try:
        yield conn
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)
