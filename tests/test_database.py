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
