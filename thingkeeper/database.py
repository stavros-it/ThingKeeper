"""SQLite connection and schema management."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name    TEXT,
    type          TEXT,
    brand         TEXT,
    model         TEXT,
    info          TEXT,
    serial        TEXT,
    store         TEXT,
    purchase_date TEXT,
    status        TEXT NOT NULL DEFAULT 'AVAILABLE',
    quantity      INTEGER NOT NULL DEFAULT 1,
    location      TEXT,
    warranty_end  TEXT,
    image_path    TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_items_group   ON items(group_name);
CREATE INDEX IF NOT EXISTS idx_items_type    ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_brand   ON items(brand);
CREATE INDEX IF NOT EXISTS idx_items_status  ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_serial  ON items(serial);
"""


def connect() -> sqlite3.Connection:
    """Open a connection with row factory and enforced foreign keys."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db() -> None:
    """Create tables / indexes if missing."""
    with connect() as conn:
        conn.executescript(_SCHEMA)
        conn.commit()


@contextmanager
def transaction():
    """Yield a connection that commits on success, rolls back on error."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
