"""Tests for thingkeeper.ui.help_dialog: shortcuts dialog and tour dialog."""

from __future__ import annotations

from thingkeeper import i18n
from thingkeeper.ui.help_dialog import ShortcutsDialog, TourDialog


def test_shortcuts_dialog_opens_english(qtbot):
    i18n.set_language("en")
    dlg = ShortcutsDialog()
    qtbot.addWidget(dlg)
    assert dlg.windowTitle() == "Keyboard shortcuts"


def test_shortcuts_dialog_opens_greek(qtbot):
    i18n.set_language("el")
    dlg = ShortcutsDialog()
    qtbot.addWidget(dlg)
    assert dlg.windowTitle() == "Συντομεύσεις πληκτρολογίου"
    i18n.set_language("en")


def test_tour_dialog_first_step_english(qtbot):
    i18n.set_language("en")
    dlg = TourDialog()
    qtbot.addWidget(dlg)
    assert "Welcome" in dlg.title_label.text()
    assert dlg.prev_btn.isEnabled() is False
    assert not dlg.next_btn.isHidden()
    assert dlg.finish_btn.isHidden()


def test_tour_dialog_first_step_greek(qtbot):
    i18n.set_language("el")
    dlg = TourDialog()
    qtbot.addWidget(dlg)
    assert "Καλώς" in dlg.title_label.text()
    i18n.set_language("en")


def test_tour_dialog_next_advances(qtbot):
    i18n.set_language("en")
    dlg = TourDialog()
    qtbot.addWidget(dlg)
    first = dlg.title_label.text()
    dlg._next()
    second = dlg.title_label.text()
    assert first != second
    assert "Welcome" not in second


def test_tour_dialog_last_step_shows_finish(qtbot):
    i18n.set_language("en")
    dlg = TourDialog()
    qtbot.addWidget(dlg)
    n = len(dlg._steps)
    for _ in range(n - 1):
        dlg._next()
    assert dlg.next_btn.isHidden()
    assert not dlg.finish_btn.isHidden()


def test_tour_dialog_prev_goes_back(qtbot):
    i18n.set_language("en")
    dlg = TourDialog()
    qtbot.addWidget(dlg)
    dlg._next()
    second = dlg.title_label.text()
    dlg._prev()
    first = dlg.title_label.text()
    assert first != second
    assert "Welcome" in first


def test_tour_dialog_prev_disabled_on_first(qtbot):
    i18n.set_language("en")
    dlg = TourDialog()
    qtbot.addWidget(dlg)
    assert dlg.prev_btn.isEnabled() is False
