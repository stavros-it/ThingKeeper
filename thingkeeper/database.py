"""SQLite connection, schema management and migrations."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from . import config

# Base schema for fresh databases. Existing databases are brought up to date
# by the migration runner in _MIGRATIONS below.
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
    deleted_at    TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS item_images (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id    INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    path       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_items_group   ON items(group_name);
CREATE INDEX IF NOT EXISTS idx_items_type    ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_brand   ON items(brand);
CREATE INDEX IF NOT EXISTS idx_items_status  ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_serial  ON items(serial);
CREATE INDEX IF NOT EXISTS idx_items_deleted ON items(deleted_at);
CREATE INDEX IF NOT EXISTS idx_images_item   ON item_images(item_id);
"""

# Latest schema version. Bump when adding a migration.
SCHEMA_VERSION = 2


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def _migration_1_add_deleted_at(conn: sqlite3.Connection) -> None:
    """v1 -> v2: add soft-delete column to items."""
    if not _column_exists(conn, "items", "deleted_at"):
        conn.execute("ALTER TABLE items ADD COLUMN deleted_at TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_items_deleted ON items(deleted_at)")


def _migration_2_add_item_images(conn: sqlite3.Connection) -> None:
    """v2 -> v3: add item_images table for multi-image attachments."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS item_images (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id    INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            path       TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_images_item ON item_images(item_id);
        """
    )


# Ordered (version, migration_fn) pairs. Each migration brings the DB from
# version N-1 to version N.
_MIGRATIONS = [
    (1, _migration_1_add_deleted_at),
    (2, _migration_2_add_item_images),
]


def _get_schema_version(conn: sqlite3.Connection) -> int:
    if not _table_exists(conn, "schema_version"):
        return 0
    row = conn.execute(
        "SELECT MAX(version) AS v FROM schema_version"
    ).fetchone()
    return int(row["v"] or 0)


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(
        "INSERT INTO schema_version (version) VALUES (?)", (version,)
    )


def connect() -> sqlite3.Connection:
    """Open a connection with row factory and enforced foreign keys."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db() -> None:
    """Create tables / indexes if missing and apply pending migrations."""
    with connect() as conn:
        conn.executescript(_SCHEMA)
        current = _get_schema_version(conn)
        for version, migration in _MIGRATIONS:
            if current < version:
                migration(conn)
                _set_schema_version(conn, version)
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
