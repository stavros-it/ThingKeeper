"""Automatic backup manager with rotation.

Creates timestamped .tkz snapshots of the inventory on launch and at a
configurable interval, keeping only the most recent N backups.

Backup folder layout:
    <backup_dir>/thingkeeper_YYYYMMDD_HHMMSS.tkz
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, QSettings, Qt, QTimer, pyqtSignal

from . import config
from .exporters import export_archive

_SETTINGS_BACKUP_DIR = "backup/dir"
_SETTINGS_BACKUP_KEEP = "backup/keep"
_SETTINGS_BACKUP_INTERVAL = "backup/interval_minutes"
_SETTINGS_BACKUP_LAST = "backup/last_run"

DEFAULT_KEEP = 10
DEFAULT_INTERVAL_MINUTES = 0


def _default_backup_dir() -> Path:
    return config.DATA_DIR / "backups"


def get_backup_dir() -> Path:
    raw = QSettings("ThingKeeper", "ThingKeeper").value(_SETTINGS_BACKUP_DIR)
    if raw:
        p = Path(raw)
    else:
        p = _default_backup_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p


def set_backup_dir(path: Path | str) -> None:
    QSettings("ThingKeeper", "ThingKeeper").setValue(_SETTINGS_BACKUP_DIR, str(path))


def get_keep() -> int:
    raw = QSettings("ThingKeeper", "ThingKeeper").value(_SETTINGS_BACKUP_KEEP)
    if raw is None:
        return DEFAULT_KEEP
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return DEFAULT_KEEP


def set_keep(keep: int) -> None:
    QSettings("ThingKeeper", "ThingKeeper").setValue(
        _SETTINGS_BACKUP_KEEP, max(1, int(keep))
    )


def get_interval_minutes() -> int:
    raw = QSettings("ThingKeeper", "ThingKeeper").value(_SETTINGS_BACKUP_INTERVAL)
    if raw is None:
        return DEFAULT_INTERVAL_MINUTES
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return DEFAULT_INTERVAL_MINUTES


def set_interval_minutes(minutes: int) -> None:
    QSettings("ThingKeeper", "ThingKeeper").setValue(
        _SETTINGS_BACKUP_INTERVAL, max(0, int(minutes))
    )


def get_last_run() -> str:
    raw = QSettings("ThingKeeper", "ThingKeeper").value(_SETTINGS_BACKUP_LAST)
    return str(raw) if raw else ""


def _stamp_now() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def _stamp_short() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def list_backups() -> list[Path]:
    """Return all .tkz backups in the backup folder, newest first."""
    d = get_backup_dir()
    files = sorted(d.glob("thingkeeper_*.tkz"), reverse=True)
    return files


def create_backup() -> Path:
    """Create a timestamped .tkz snapshot and rotate out old ones."""
    d = get_backup_dir()
    d.mkdir(parents=True, exist_ok=True)
    name = f"thingkeeper_{_stamp_now()}{config.ARCHIVE_EXT}"
    path = d / name
    export_archive(path)
    QSettings("ThingKeeper", "ThingKeeper").setValue(
        _SETTINGS_BACKUP_LAST, _stamp_short()
    )
    rotate_backups()
    return path


def rotate_backups() -> int:
    """Delete oldest backups beyond `keep`, return count removed."""
    keep = get_keep()
    backups = list_backups()
    removed = 0
    for old in backups[keep:]:
        try:
            old.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def maybe_auto_backup() -> Path | None:
    """Run a backup if interval has elapsed since the last one.

    Returns the backup path if one was created, else None.
    """
    interval = get_interval_minutes()
    if interval <= 0:
        return None
    last = get_last_run()
    if last:
        try:
            last_dt = datetime.strptime(last, "%Y%m%d_%H%M%S")
            elapsed_min = (datetime.now() - last_dt).total_seconds() / 60.0
            if elapsed_min < interval:
                return None
        except ValueError:
            pass
    try:
        return create_backup()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Auto-backup failed")
        return None


class BackupScheduler(QObject):
    """Qt timer-based scheduler for periodic backups."""

    backup_created = pyqtSignal(str)
    backup_failed = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.VeryCoarseTimer)
        self._timer.timeout.connect(self._tick)
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        interval = get_interval_minutes()
        if interval <= 0:
            return
        self._timer.start(interval * 60 * 1000)
        self._running = True

    def stop(self) -> None:
        self._timer.stop()
        self._running = False

    def restart(self) -> None:
        self.stop()
        self.start()

    def _tick(self) -> None:
        try:
            path = create_backup()
            self.backup_created.emit(str(path))
        except Exception as exc:
            self.backup_failed.emit(str(exc))


def backup_age_seconds(path: Path) -> float:
    """Return age of a backup file in seconds."""
    try:
        return time.time() - path.stat().st_mtime
    except OSError:
        return float("inf")
