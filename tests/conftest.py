"""Shared pytest fixtures for ThingKeeper tests.

Every test runs against a fresh, temporary data directory so the real
inventory in `./data/` is never touched. GUI tests use the offscreen Qt
platform so they can run headless in CI.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path_factory, monkeypatch):
    """Point THINGKEEPER_DATA at a per-test temp dir and reload config.

    This ensures every test starts with an empty database and attachments
    folder, regardless of what's in ./data/.
    """
    tmp = tmp_path_factory.mktemp("tk_data")
    monkeypatch.setenv("THINGKEEPER_DATA", str(tmp))
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    # Reload all modules that cache paths at import time.
    import thingkeeper.config as config
    importlib.reload(config)
    import thingkeeper.database as database
    importlib.reload(database)
    import thingkeeper.repository as repository
    importlib.reload(repository)
    import thingkeeper.importers as importers
    importlib.reload(importers)
    import thingkeeper.exporters as exporters
    importlib.reload(exporters)
    import thingkeeper.backup as backup
    importlib.reload(backup)
    import thingkeeper.integrity as integrity
    importlib.reload(integrity)
    import thingkeeper.commands as commands
    importlib.reload(commands)
    import thingkeeper.scanner as scanner
    importlib.reload(scanner)

    # Clear any cached QSettings so tests start from defaults.
    from PyQt6.QtCore import QSettings
    QSettings("ThingKeeper", "ThingKeeper").clear()

    yield tmp

    # Reset PYTHONPATH-level state for the next test.
    QSettings("ThingKeeper", "ThingKeeper").clear()


@pytest.fixture
def db(isolated_data_dir):
    """Initialise a fresh database and return the database module."""
    from thingkeeper import database
    database.init_db()
    return database


@pytest.fixture
def repo(db):
    """Return the repository module with an initialised DB."""
    from thingkeeper import repository
    return repository


@pytest.fixture
def qtbot(qtbot):
    """Pass through pytest-qt's qtbot fixture for GUI tests."""
    return qtbot


@pytest.fixture
def sample_item():
    """Return a factory that builds Item instances with sensible defaults."""
    from thingkeeper.repository import Item

    def _make(**overrides) -> Item:
        defaults = dict(
            group_name="IT",
            type="laptop",
            brand="Dell",
            model="XPS 13",
            serial="TEST-001",
            status="AVAILABLE",
            quantity=1,
            location="Office",
            store="Store",
            info="Notes",
            purchase_date="2024-01-15",
            warranty_end="2027-01-15",
            unit_price=1500.00,
            depreciation_years=5.0,
        )
        defaults.update(overrides)
        return Item(**defaults)

    return _make


@pytest.fixture
def excel_path():
    """Path to the test Excel file (406 rows). Skips if missing."""
    p = Path("My Equipment.xlsx")
    if not p.exists():
        pytest.skip("My Equipment.xlsx not available")
    return p


class _FakeMessageBox:
    """Drop-in for QMessageBox that never blocks.

    Methods return StandardButton values that represent 'yes'/'ok' so
    tests can exercise code paths that normally prompt the user.
    """

    @staticmethod
    def information(*args, **kwargs):
        from PyQt6.QtWidgets import QMessageBox
        return QMessageBox.StandardButton.Ok

    @staticmethod
    def warning(*args, **kwargs):
        from PyQt6.QtWidgets import QMessageBox
        return QMessageBox.StandardButton.Ok

    @staticmethod
    def critical(*args, **kwargs):
        from PyQt6.QtWidgets import QMessageBox
        return QMessageBox.StandardButton.Ok

    @staticmethod
    def question(*args, **kwargs):
        from PyQt6.QtWidgets import QMessageBox
        return QMessageBox.StandardButton.Yes

    @staticmethod
    def about(*args, **kwargs):
        return None


@pytest.fixture
def fake_msgbox(monkeypatch):
    """Patch QMessageBox in main_window so it never blocks."""
    import thingkeeper.ui.main_window as mw_mod
    monkeypatch.setattr(mw_mod, "QMessageBox", _FakeMessageBox)
    return _FakeMessageBox


# Ensure the project root is on sys.path so `import thingkeeper` works
# even when pytest is invoked from a subdirectory.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
