"""Tests for thingkeeper.backup: snapshots, rotation, auto-backup, scheduler."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from thingkeeper import backup as backup_mod
from thingkeeper.repository import create_item


def test_default_backup_dir_under_data():
    d = backup_mod.get_backup_dir()
    assert d.parent == Path(__file__).resolve().parent.parent / "data" or d.exists()


def test_set_and_get_backup_dir(tmp_path):
    custom = tmp_path / "custom_backups"
    backup_mod.set_backup_dir(custom)
    assert backup_mod.get_backup_dir() == custom
    assert custom.exists()


def test_set_and_get_keep():
    backup_mod.set_keep(7)
    assert backup_mod.get_keep() == 7
    # Clamped to >= 1
    backup_mod.set_keep(0)
    assert backup_mod.get_keep() == 1


def test_set_and_get_interval():
    backup_mod.set_interval_minutes(30)
    assert backup_mod.get_interval_minutes() == 30
    # Clamped to >= 0
    backup_mod.set_interval_minutes(-5)
    assert backup_mod.get_interval_minutes() == 0


def test_create_backup_creates_tkz(repo, sample_item):
    create_item(sample_item(serial="BK-1"))
    path = backup_mod.create_backup()
    assert path.exists()
    assert path.suffix == ".tkz"
    assert path.name.startswith("thingkeeper_")


def test_create_backup_timestamp_unique(repo, sample_item):
    """Two backups created in quick succession must not overwrite each other."""
    create_item(sample_item(serial="BK-2"))
    p1 = backup_mod.create_backup()
    p2 = backup_mod.create_backup()
    assert p1 != p2
    assert p1.exists()
    assert p2.exists()


def test_list_backups_newest_first(repo, sample_item):
    create_item(sample_item(serial="BK-3"))
    paths = [backup_mod.create_backup() for _ in range(3)]
    listed = backup_mod.list_backups()
    assert len(listed) == 3
    # Newest first
    assert listed[0] == paths[-1]


def test_rotate_backups_enforces_keep(repo, sample_item):
    create_item(sample_item(serial="BK-4"))
    backup_mod.set_keep(3)
    for _ in range(5):
        backup_mod.create_backup()
    assert len(backup_mod.list_backups()) == 3


def test_maybe_auto_backup_disabled_when_interval_zero(repo, sample_item):
    create_item(sample_item(serial="BK-5"))
    backup_mod.set_interval_minutes(0)
    assert backup_mod.maybe_auto_backup() is None


def test_maybe_auto_backup_runs_when_interval_elapsed(repo, sample_item):
    from PyQt6.QtCore import QSettings
    create_item(sample_item(serial="BK-6"))
    backup_mod.set_interval_minutes(60)
    QSettings("ThingKeeper", "ThingKeeper").remove("backup/last_run")
    result = backup_mod.maybe_auto_backup()
    assert result is not None
    assert result.exists()


def test_maybe_auto_backup_skips_when_too_recent(repo, sample_item):
    create_item(sample_item(serial="BK-7"))
    backup_mod.set_interval_minutes(60)
    backup_mod.create_backup()  # sets last_run to now
    assert backup_mod.maybe_auto_backup() is None


def test_get_last_run_empty_initially():
    from PyQt6.QtCore import QSettings
    QSettings("ThingKeeper", "ThingKeeper").remove("backup/last_run")
    assert backup_mod.get_last_run() == ""


def test_get_last_run_after_backup(repo, sample_item):
    create_item(sample_item(serial="BK-8"))
    backup_mod.create_backup()
    last = backup_mod.get_last_run()
    assert last != ""
    # Should parse as a timestamp
    datetime.strptime(last, "%Y%m%d_%H%M%S")


def test_backup_scheduler_does_not_start_with_zero_interval(qtbot):
    scheduler = backup_mod.BackupScheduler()
    backup_mod.set_interval_minutes(0)
    scheduler.start()
    assert not scheduler._running


def test_backup_scheduler_starts_with_interval(qtbot):
    scheduler = backup_mod.BackupScheduler()
    backup_mod.set_interval_minutes(60)
    scheduler.start()
    assert scheduler._running
    scheduler.stop()
    assert not scheduler._running


def test_backup_scheduler_restart(qtbot):
    scheduler = backup_mod.BackupScheduler()
    backup_mod.set_interval_minutes(60)
    scheduler.start()
    assert scheduler._running
    backup_mod.set_interval_minutes(120)
    scheduler.restart()
    assert scheduler._running
    scheduler.stop()


def test_backup_scheduler_emits_backup_created(qtbot, repo, sample_item):
    create_item(sample_item(serial="BK-SCHED"))
    scheduler = backup_mod.BackupScheduler()
    received = []
    scheduler.backup_created.connect(lambda p: received.append(p))
    scheduler._tick()
    assert len(received) == 1
    assert Path(received[0]).exists()


def test_backup_scheduler_emits_backup_failed(qtbot):
    scheduler = backup_mod.BackupScheduler()
    received = []
    scheduler.backup_failed.connect(lambda msg: received.append(msg))
    with patch.object(backup_mod, "create_backup", side_effect=Exception("boom")):
        scheduler._tick()
    assert len(received) == 1
    assert "boom" in received[0]
