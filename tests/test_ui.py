"""GUI tests for thingkeeper.ui: main window construction and dialogs.

These tests use the offscreen Qt platform so they run headless in CI.
Modal dialogs (which would block) are exercised by mocking QMessageBox.
"""

from __future__ import annotations

from thingkeeper.repository import create_item


def test_main_window_constructs(qtbot, db, fake_msgbox, sample_item):
    from thingkeeper.ui.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    assert w.table.rowCount() == 0
    assert w.windowTitle().startswith("ThingKeeper")


def test_main_window_shows_items(qtbot, db, fake_msgbox, sample_item):
    from thingkeeper.ui.main_window import MainWindow
    for i in range(5):
        create_item(sample_item(serial=f"UI-{i:03d}"))
    w = MainWindow()
    qtbot.addWidget(w)
    assert w.table.rowCount() == 5


def test_settings_dialog_constructs(qtbot, db, fake_msgbox):
    from thingkeeper.ui.settings_dialog import SettingsDialog
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    assert dlg.dir_edit.text()
    assert dlg.keep_spin.value() >= 1


def test_integrity_dialog_clean_db(qtbot, db, fake_msgbox):
    from thingkeeper.ui.integrity_dialog import IntegrityDialog
    dlg = IntegrityDialog()
    qtbot.addWidget(dlg)
    assert dlg._report.ok


def test_dashboard_dialog_constructs(qtbot, db, fake_msgbox, sample_item):
    from thingkeeper.ui.dashboard_dialog import DashboardDialog
    from thingkeeper.ui.main_window import MainWindow
    for i in range(3):
        create_item(sample_item(serial=f"DASH-{i}"))
    w = MainWindow()
    qtbot.addWidget(w)
    dlg = DashboardDialog(w)
    qtbot.addWidget(dlg)


def test_report_builder_dialog_constructs(qtbot, db, fake_msgbox, sample_item):
    from thingkeeper.ui.main_window import MainWindow
    from thingkeeper.ui.report_builder_dialog import ReportBuilderDialog
    create_item(sample_item(serial="RB-1"))
    w = MainWindow()
    qtbot.addWidget(w)
    dlg = ReportBuilderDialog(w)
    qtbot.addWidget(dlg)


def test_bulk_edit_dialog_constructs(qtbot, db, fake_msgbox, sample_item):
    from thingkeeper.ui.bulk_edit_dialog import BulkEditDialog
    from thingkeeper.ui.main_window import MainWindow
    for i in range(3):
        create_item(sample_item(serial=f"BE-{i}"))
    w = MainWindow()
    qtbot.addWidget(w)
    w.table.selectRow(0)
    dlg = BulkEditDialog(w, [1])
    qtbot.addWidget(dlg)


def test_trash_dialog_constructs(qtbot, db, fake_msgbox):
    from thingkeeper.ui.trash_dialog import TrashDialog
    dlg = TrashDialog()
    qtbot.addWidget(dlg)


def test_scan_dialog_constructs(qtbot, db, fake_msgbox):
    from thingkeeper.ui.scan_dialog import ScanDialog
    dlg = ScanDialog()
    qtbot.addWidget(dlg)


def test_contacts_dialog_constructs(qtbot, db, fake_msgbox):
    from thingkeeper.ui.contacts_dialog import ContactsDialog
    dlg = ContactsDialog()
    qtbot.addWidget(dlg)


def test_main_window_backup_now(qtbot, db, fake_msgbox, sample_item):
    from thingkeeper import backup as backup_mod
    from thingkeeper.ui.main_window import MainWindow
    backup_mod.set_interval_minutes(0)
    create_item(sample_item(serial="BN-1"))
    w = MainWindow()
    qtbot.addWidget(w)
    w.backup_now()
    assert len(backup_mod.list_backups()) >= 1


def test_main_window_scheduler_starts(qtbot, db, fake_msgbox):
    from thingkeeper import backup as backup_mod
    from thingkeeper.ui.main_window import MainWindow
    backup_mod.set_interval_minutes(60)
    w = MainWindow()
    qtbot.addWidget(w)
    assert w._backup_scheduler._running
    w._backup_scheduler.stop()
