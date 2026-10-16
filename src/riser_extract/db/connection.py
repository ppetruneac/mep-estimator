"""SQLite connection helpers.

Concurrency
-----------
We enable WAL mode + a busy timeout so multiple ingest/export processes can
open the same ``getriser.sqlite`` file. Writers serialize via SQLite's lock;
readers do not block each other under WAL. Use short transactions and
``BEGIN IMMEDIATE`` when writing.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from riser_extract.config import db_path

_SCHEMA = Path(__file__).with_name("schema.sql")

# Wait up to 30s when another writer holds the lock (multi-process ingest).
BUSY_TIMEOUT_MS = 30_000


def connect(path: Path | None = None, *, readonly: bool = False) -> sqlite3.Connection:
    target = path or db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if readonly and target.exists():
        uri = f"file:{target}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=BUSY_TIMEOUT_MS / 1000.0)
    else:
        conn = sqlite3.connect(str(target), timeout=BUSY_TIMEOUT_MS / 1000.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    if not readonly:
        # WAL allows concurrent readers while a writer is active.
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def migrate(conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    own = conn is None
    c = conn or connect()
    sql = _SCHEMA.read_text(encoding="utf-8")
    c.executescript(sql)
    c.commit()
    if own:
        return c
    return c
