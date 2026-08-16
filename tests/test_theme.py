"""Tests for thingkeeper.ui.theme: dark palette and styling."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette

from thingkeeper.ui.theme import (
    ACCENT,
    BG_BASE,
    BG_WINDOW,
    TEXT,
    apply_theme,
    dark_palette,
    refresh_theme,
)


def test_dark_palette_has_dark_window():
    pal = dark_palette()
    window = pal.color(QPalette.ColorRole.Window)
    assert window == QColor(BG_WINDOW)


def test_dark_palette_has_dark_base():
    pal = dark_palette()
    base = pal.color(QPalette.ColorRole.Base)
    assert base == QColor(BG_BASE)


def test_dark_palette_has_light_text():
    pal = dark_palette()
    text = pal.color(QPalette.ColorRole.Text)
    assert text == QColor(TEXT)


def test_dark_palette_highlight_is_accent():
    pal = dark_palette()
    highlight = pal.color(QPalette.ColorRole.Highlight)
    assert highlight == QColor(ACCENT)


def test_apply_theme_sets_palette(qtbot):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    assert app is not None
    apply_theme(app)
    assert app.palette().color(QPalette.ColorRole.Window) == QColor(BG_WINDOW)


def test_apply_theme_sets_fusion_style(qtbot):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    assert app is not None
    apply_theme(app)
    assert app.style().objectName().lower() in ("fusion", "")


def test_apply_theme_sets_stylesheet(qtbot):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    assert app is not None
    apply_theme(app)
    assert app.styleSheet()


def test_refresh_theme_updates_widgets(qtbot, db, fake_msgbox):
    from PyQt6.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance()
    assert app is not None
    apply_theme(app)
    w = QMainWindow()
    qtbot.addWidget(w)
    refresh_theme()
    assert w.palette().color(QPalette.ColorRole.Window) == QColor(BG_WINDOW)


def test_main_window_uses_dark_palette(qtbot, db, fake_msgbox):
    from thingkeeper.ui.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    assert w.palette().color(QPalette.ColorRole.Window) == QColor(BG_WINDOW)
