"""Theme module: light/dark palettes and QSS stylesheet.

Follows the system palette by default, with a manual override stored in
QSettings("ThingKeeper"). Use `apply_theme(app)` at startup and
`set_theme_mode(mode)` to change at runtime.
"""

from __future__ import annotations

from enum import Enum

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


class ThemeMode(str, Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


_SETTINGS_KEY = "theme/mode"

_QSS = """
QMainWindow, QDialog { background: palette(window); }
QTableWidget {
    gridline-color: palette(mid);
    selection-background-color: palette(highlight);
    selection-color: palette(highlighted-text);
}
QTableWidget::item:alternate { background: palette(alternate-base); }
QToolBar { spacing: 4px; padding: 4px; border: none; }
QStatusBar { border-top: 1px solid palette(mid); }
QMenuBar { border-bottom: 1px solid palette(mid); }
QPushButton {
    padding: 4px 12px;
    min-height: 20px;
}
QPushButton:default { border: 2px solid palette(highlight); }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    padding: 3px 6px;
    min-height: 20px;
}
QGroupBox {
    border: 1px solid palette(mid);
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QCheckBox { spacing: 6px; }
"""


def _light_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor("#f4f4f4"))
    p.setColor(QPalette.ColorRole.WindowText, QColor("#222222"))
    p.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor("#f0f0f0"))
    p.setColor(QPalette.ColorRole.Text, QColor("#222222"))
    p.setColor(QPalette.ColorRole.Button, QColor("#e4e4e4"))
    p.setColor(QPalette.ColorRole.ButtonText, QColor("#222222"))
    p.setColor(QPalette.ColorRole.Highlight, QColor("#1f5fa8"))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffdc"))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor("#222222"))
    return p


def _dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor("#2b2b2b"))
    p.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    p.setColor(QPalette.ColorRole.Base, QColor("#1e1e1e"))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor("#262626"))
    p.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    p.setColor(QPalette.ColorRole.Button, QColor("#3a3a3a"))
    p.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    p.setColor(QPalette.ColorRole.Highlight, QColor("#1f5fa8"))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#3c3c3c"))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0e0"))
    p.setColor(QPalette.ColorRole.Link, QColor("#6ab0f3"))
    p.setColor(QPalette.ColorRole.LinkVisited, QColor("#a06ab0"))
    return p


def get_theme_mode() -> ThemeMode:
    raw = QSettings("ThingKeeper", "ThingKeeper").value(_SETTINGS_KEY)
    if raw in (ThemeMode.LIGHT.value, ThemeMode.DARK.value):
        return ThemeMode(raw)
    return ThemeMode.SYSTEM


def set_theme_mode(mode: ThemeMode) -> None:
    QSettings("ThingKeeper", "ThingKeeper").setValue(_SETTINGS_KEY, mode.value)


def _system_is_dark() -> bool:
    """Detect dark mode by checking the system's default text vs window colour."""
    app = QApplication.instance()
    if app is None:
        return False
    pal = app.style().standardPalette() if app.style() else QPalette()
    text = pal.color(QPalette.ColorRole.Text)
    window = pal.color(QPalette.ColorRole.Window)
    return text.lightness() > window.lightness()


def _resolve_palette(mode: ThemeMode) -> QPalette:
    if mode == ThemeMode.LIGHT:
        return _light_palette()
    if mode == ThemeMode.DARK:
        return _dark_palette()
    if _system_is_dark():
        return _dark_palette()
    return _light_palette()


def apply_theme(app: QApplication) -> None:
    """Apply the current theme to the given QApplication."""
    pal = _resolve_palette(get_theme_mode())
    app.setPalette(pal)
    app.setStyleSheet(_QSS)


def refresh_theme() -> None:
    """Re-apply the theme to all top-level widgets."""
    app = QApplication.instance()
    if app is not None:
        apply_theme(app)
        for w in app.topLevelWidgets():
            w.setPalette(app.palette())
