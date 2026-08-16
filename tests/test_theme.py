"""Tests for thingkeeper.ui.theme: palettes and theme switching."""

from __future__ import annotations

from thingkeeper.ui.theme import (
    ThemeMode,
    _dark_palette,
    _light_palette,
    _resolve_palette,
    apply_theme,
    get_theme_mode,
    refresh_theme,
    set_theme_mode,
)


def test_default_mode_is_system():
    from PyQt6.QtCore import QSettings
    QSettings("ThingKeeper", "ThingKeeper").remove("theme/mode")
    assert get_theme_mode() == ThemeMode.SYSTEM


def test_set_and_get_mode():
    set_theme_mode(ThemeMode.DARK)
    assert get_theme_mode() == ThemeMode.DARK
    set_theme_mode(ThemeMode.LIGHT)
    assert get_theme_mode() == ThemeMode.LIGHT
    set_theme_mode(ThemeMode.SYSTEM)
    assert get_theme_mode() == ThemeMode.SYSTEM


def test_light_palette_has_light_window():
    pal = _light_palette()
    window = pal.color(__import__("PyQt6").QtGui.QPalette.ColorRole.Window)
    assert window.lightness() > 200


def test_dark_palette_has_dark_window():
    from PyQt6.QtGui import QPalette
    pal = _dark_palette()
    window = pal.color(QPalette.ColorRole.Window)
    assert window.lightness() < 80


def test_resolve_palette_explicit_light():
    pal = _resolve_palette(ThemeMode.LIGHT)
    from PyQt6.QtGui import QPalette
    assert pal.color(QPalette.ColorRole.Window).lightness() > 200


def test_resolve_palette_explicit_dark():
    from PyQt6.QtGui import QPalette
    pal = _resolve_palette(ThemeMode.DARK)
    assert pal.color(QPalette.ColorRole.Window).lightness() < 80


def test_apply_theme_sets_palette(qtbot):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    assert app is not None
    set_theme_mode(ThemeMode.DARK)
    apply_theme(app)
    from PyQt6.QtGui import QPalette
    assert app.palette().color(QPalette.ColorRole.Window).lightness() < 80


def test_refresh_theme_updates_widgets(qtbot, db, fake_msgbox):
    from thingkeeper.ui.main_window import MainWindow
    set_theme_mode(ThemeMode.LIGHT)
    w = MainWindow()
    qtbot.addWidget(w)
    set_theme_mode(ThemeMode.DARK)
    refresh_theme()
    from PyQt6.QtGui import QPalette
    assert w.palette().color(QPalette.ColorRole.Window).lightness() < 80


def test_theme_menu_actions_exist(qtbot, db, fake_msgbox):
    from thingkeeper.ui.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    assert hasattr(w, "_theme_group")
    assert len(w._theme_group.actions()) == 3
