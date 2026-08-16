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
    unit_price    REAL,
    depreciation_years REAL,
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

CREATE TABLE IF NOT EXISTS contacts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    phone      TEXT,
    email      TEXT,
    notes      TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS loans (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id      INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    contact_id   INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
    borrower     TEXT NOT NULL,
    loaned_on    TEXT NOT NULL DEFAULT (date('now')),
    due_on       TEXT,
    returned_on  TEXT,
    notes        TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_items_group   ON items(group_name);
CREATE INDEX IF NOT EXISTS idx_items_type    ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_brand   ON items(brand);
CREATE INDEX IF NOT EXISTS idx_items_status  ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_serial  ON items(serial);
CREATE INDEX IF NOT EXISTS idx_items_deleted ON items(deleted_at);
CREATE INDEX IF NOT EXISTS idx_images_item   ON item_images(item_id);
CREATE INDEX IF NOT EXISTS idx_loans_item    ON loans(item_id);
CREATE INDEX IF NOT EXISTS idx_loans_contact ON loans(contact_id);
CREATE INDEX IF NOT EXISTS idx_loans_open    ON loans(returned_on);
"""

# Latest schema version. Bump when adding a migration.
SCHEMA_VERSION = 5


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def _migration_1_add_deleted_at(conn: sqlite3.Connection) -> None:
    """v0 -> v1: add soft-delete column to items."""
    if not _column_exists(conn, "items", "deleted_at"):
        conn.execute("ALTER TABLE items ADD COLUMN deleted_at TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_items_deleted ON items(deleted_at)")


def _migration_2_add_item_images(conn: sqlite3.Connection) -> None:
    """v1 -> v2: add item_images table for multi-image attachments."""
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


def _migration_3_add_contacts(conn: sqlite3.Connection) -> None:
    """v2 -> v3: add contacts table for loan tracking."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS contacts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            phone      TEXT,
            email      TEXT,
            notes      TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )


def _migration_4_add_loans(conn: sqlite3.Connection) -> None:
    """v3 -> v4: add loans table for loan tracking."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS loans (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id      INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            contact_id   INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
            borrower     TEXT NOT NULL,
            loaned_on    TEXT NOT NULL DEFAULT (date('now')),
            due_on       TEXT,
            returned_on  TEXT,
            notes        TEXT,
            created_at   TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_loans_item    ON loans(item_id);
        CREATE INDEX IF NOT EXISTS idx_loans_contact ON loans(contact_id);
        CREATE INDEX IF NOT EXISTS idx_loans_open    ON loans(returned_on);
        """
    )


def _migration_5_add_price_depreciation(conn: sqlite3.Connection) -> None:
    """v4 -> v5: add unit_price and depreciation_years to items."""
    if not _column_exists(conn, "items", "unit_price"):
        conn.execute("ALTER TABLE items ADD COLUMN unit_price REAL")
    if not _column_exists(conn, "items", "depreciation_years"):
        conn.execute("ALTER TABLE items ADD COLUMN depreciation_years REAL")


# Ordered (version, migration_fn) pairs. Each migration brings the DB from
# version N-1 to version N.
_MIGRATIONS = [
    (1, _migration_1_add_deleted_at),
    (2, _migration_2_add_item_images),
    (3, _migration_3_add_contacts),
    (4, _migration_4_add_loans),
    (5, _migration_5_add_price_depreciation),
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
