"""Tests for thingkeeper.database: schema, migrations, init_db."""

from __future__ import annotations

from thingkeeper import config


def test_init_db_creates_schema(db):
    conn = db.connect()
    try:
        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {"items", "item_images", "contacts", "loans"} <= tables
    finally:
        conn.close()


def test_schema_version_is_5(db):
    conn = db.connect()
    try:
        assert db._get_schema_version(conn) == 5
    finally:
        conn.close()


def test_init_db_is_idempotent(db):
    db.init_db()
    db.init_db()
    conn = db.connect()
    try:
        assert db._get_schema_version(conn) == 5
    finally:
        conn.close()


def test_new_columns_exist(db):
    conn = db.connect()
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(items)")}
        assert "unit_price" in cols
        assert "depreciation_years" in cols
        assert "deleted_at" in cols
    finally:
        conn.close()


def test_wal_mode_enabled(db):
    conn = db.connect()
    try:
        row = conn.execute("PRAGMA journal_mode").fetchone()
        assert row[0].lower() == "wal"
    finally:
        conn.close()


def test_db_path_inside_data_dir(db):
    assert config.DB_PATH.parent == config.DATA_DIR


def test_transaction_context_manager(db):
    with db.transaction() as conn:
        conn.execute(
            "INSERT INTO items (group_name, type, brand, model, serial) "
            "VALUES (?, ?, ?, ?, ?)",
            ("IT", "laptop", "Dell", "XPS", "TX-001"),
        )
    conn = db.connect()
    try:
        row = conn.execute(
            "SELECT serial FROM items WHERE serial = ?", ("TX-001",)
        ).fetchone()
        assert row is not None and row[0] == "TX-001"
    finally:
        conn.close()


def test_init_db_on_v0_legacy_schema(db, isolated_data_dir):
    """Regression: a v0 DB (items without deleted_at, empty schema_version)
    must be brought up to v5 by init_db without errors.

    Previously _SCHEMA tried to create idx_items_deleted before migration 1
    had a chance to add the deleted_at column, crashing with
    'no such column: deleted_at'.
    """
    import sqlite3

    from thingkeeper import config

    # Drop and recreate a minimal v0-style items table.
    conn = sqlite3.connect(config.DB_PATH)
    try:
        conn.executescript(
            """
            DROP TABLE IF EXISTS loans;
            DROP TABLE IF EXISTS contacts;
            DROP TABLE IF EXISTS item_images;
            DROP TABLE IF EXISTS schema_version;
            DROP TABLE IF EXISTS items;
            CREATE TABLE items (
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
            INSERT INTO items (group_name, type, brand, model, serial)
            VALUES ('IT', 'laptop', 'Dell', 'XPS', 'LEGACY-001');
            """
        )
        conn.commit()
    finally:
        conn.close()

    # Reinit: must not raise.
    db.init_db()

    conn = db.connect()
    try:
        # Migration 1 added deleted_at.
        cols = {r[1] for r in conn.execute("PRAGMA table_info(items)")}
        assert "deleted_at" in cols
        assert "unit_price" in cols
        assert "depreciation_years" in cols
        # Schema version is now 5.
        assert db._get_schema_version(conn) == 5
        # The legacy row survived.
        row = conn.execute(
            "SELECT serial FROM items WHERE serial = ?", ("LEGACY-001",)
        ).fetchone()
        assert row is not None
        # The idx_items_deleted index exists.
        idx = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_items_deleted'"
        ).fetchone()
        assert idx is not None
    finally:
        conn.close()
