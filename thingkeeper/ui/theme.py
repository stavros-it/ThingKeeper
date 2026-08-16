"""Theme module: polished dark palette and QSS stylesheet.

Single dark theme applied unconditionally at startup via `apply_theme(app)`.
Call `refresh_theme()` to re-apply after dynamic widget changes.
"""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QWidget

# Accent color used for highlights, links, default-button borders.
ACCENT = "#3b82f6"
ACCENT_HOVER = "#60a5fa"
ACCENT_PRESSED = "#2563eb"

# Core palette.
BG_WINDOW = "#1e1e1e"
BG_BASE = "#181818"
BG_ALT = "#1f1f1f"
BG_BUTTON = "#2a2a2a"
BG_BUTTON_HOVER = "#333333"
BG_BUTTON_PRESSED = "#3f3f3f"
TEXT = "#e4e4e4"
TEXT_DIM = "#9a9a9a"
TEXT_BRIGHT = "#ffffff"
BORDER = "#3a3a3a"
BORDER_FOCUS = ACCENT

# Semantic colors (readable on dark backgrounds).
SUCCESS = "#4ade80"
SUCCESS_BG = "#16331f"
WARNING = "#fbbf24"
WARNING_BG = "#3a2f10"
DANGER = "#f87171"
DANGER_BG = "#3a1c1c"
INFO = "#60a5fa"
INFO_BG = "#1a2845"
MUTED = "#9a9a9a"

# Status colors tuned for dark backgrounds.
STATUS_COLORS = {
    "AVAILABLE": SUCCESS,
    "IN USE": INFO,
    "LOANED": WARNING,
    "BROKEN": DANGER,
    "SOLD": MUTED,
}
DEFAULT_STATUS_COLOR = TEXT

_QSS = f"""
* {{ outline: 0; }}

QMainWindow, QDialog {{
    background: {BG_WINDOW};
}}

QWidget {{
    color: {TEXT};
    font-family: "Segoe UI", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

QLabel {{
    background: transparent;
    color: {TEXT};
}}
QLabel:disabled {{ color: {TEXT_DIM}; }}

/* ---- Toolbars ---- */
QToolBar {{
    background: {BG_WINDOW};
    border: none;
    border-bottom: 1px solid {BORDER};
    spacing: 4px;
    padding: 6px 8px;
    min-height: 38px;
}}
QToolBar::separator {{
    background: {BORDER};
    width: 1px;
    margin: 4px 6px;
}}
QToolBar QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 6px 10px;
    min-width: 28px;
    min-height: 24px;
    color: {TEXT};
}}
QToolBar QToolButton:hover {{
    background: {BG_BUTTON_HOVER};
    border-color: {BORDER};
}}
QToolBar QToolButton:pressed,
QToolBar QToolButton:checked {{
    background: {BG_BUTTON_PRESSED};
    border-color: {ACCENT};
}}
QToolBar QToolButton:disabled {{ color: {TEXT_DIM}; }}

/* ---- Menus ---- */
QMenuBar {{
    background: {BG_WINDOW};
    border-bottom: 1px solid {BORDER};
    padding: 2px;
    min-height: 26px;
}}
QMenuBar::item {{
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background: {BG_BUTTON_HOVER};
}}
QMenu {{
    background: {BG_BASE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px;
}}
QMenu::item {{
    padding: 6px 24px 6px 18px;
    border-radius: 4px;
    margin: 1px 4px;
}}
QMenu::item:selected {{
    background: {ACCENT};
    color: {TEXT_BRIGHT};
}}
QMenu::item:disabled {{ color: {TEXT_DIM}; }}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 4px 8px;
}}

/* ---- Tables ---- */
QTableWidget {{
    background: {BG_BASE};
    alternate-background-color: {BG_ALT};
    color: {TEXT};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: 6px;
    selection-background-color: {ACCENT};
    selection-color: {TEXT_BRIGHT};
    outline: 0;
}}
QTableWidget::item {{
    padding: 4px 8px;
    border: none;
}}
QTableWidget::item:selected {{
    background: {ACCENT};
    color: {TEXT_BRIGHT};
}}
QTableWidget::item:selected:!focus {{
    background: {ACCENT_HOVER};
}}
QHeaderView::section {{
    background: {BG_BUTTON};
    color: {TEXT};
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
}}
QHeaderView::section:horizontal:first {{ border-top-left-radius: 6px; }}
QHeaderView::section:horizontal:last {{ border-top-right-radius: 6px; border-right: none; }}
QTableCornerButton::section {{
    background: {BG_BUTTON};
    border: none;
    border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    border-top-left-radius: 6px;
}}

QAbstractScrollArea QScrollBar:vertical {{
    background: {BG_BASE};
    width: 12px;
    border-left: 1px solid {BORDER};
}}
QAbstractScrollArea QScrollBar:horizontal {{
    background: {BG_BASE};
    height: 12px;
    border-top: 1px solid {BORDER};
}}
QScrollBar::handle {{
    background: #5a5a5a;
    border: 2px solid {BG_BASE};
    border-radius: 4px;
    min-height: 24px;
    min-width: 24px;
}}
QScrollBar::handle:hover {{ background: #707070; }}
QScrollBar::handle:pressed {{ background: {ACCENT}; }}
QScrollBar::sub-line, QScrollBar::add-line {{
    border: none; background: none; height: 0; width: 0;
}}
QScrollBar::sub-page, QScrollBar::add-page {{ background: none; }}

/* ---- Inputs ---- */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {BG_BASE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 5px 8px;
    min-height: 22px;
    selection-background-color: {ACCENT};
    selection-color: {TEXT_BRIGHT};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {BORDER_FOCUS};
}}
QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled,
QSpinBox:disabled, QDoubleSpinBox:disabled {{
    color: {TEXT_DIM};
    background: {BG_WINDOW};
}}

/* ComboBox dropdown */
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border: none;
    border-left: 1px solid {BORDER};
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    background: {BG_BUTTON};
}}
QComboBox::drop-down:hover {{ background: {BG_BUTTON_HOVER}; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {TEXT};
    width: 0;
    height: 0;
    margin-left: -4px;
}}
QComboBox QAbstractItemView {{
    background: {BG_BASE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
    outline: 0;
    selection-background-color: {ACCENT};
    selection-color: {TEXT_BRIGHT};
}}

/* SpinBox arrows */
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: {BG_BUTTON};
    border: none;
    width: 18px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {BG_BUTTON_HOVER};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid {TEXT};
    width: 0; height: 0;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {TEXT};
    width: 0; height: 0;
}}

/* ---- Buttons ---- */
QPushButton {{
    background: {BG_BUTTON};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 6px 16px;
    min-width: 64px;
    min-height: 22px;
}}
QPushButton:hover {{
    background: {BG_BUTTON_HOVER};
    border-color: {TEXT_DIM};
}}
QPushButton:pressed {{
    background: {BG_BUTTON_PRESSED};
    border-color: {ACCENT};
}}
QPushButton:default {{
    background: {ACCENT};
    border: 1px solid {ACCENT_PRESSED};
    color: {TEXT_BRIGHT};
    font-weight: 600;
}}
QPushButton:default:hover {{
    background: {ACCENT_HOVER};
    border-color: {ACCENT_HOVER};
}}
QPushButton:default:pressed {{
    background: {ACCENT_PRESSED};
    border-color: {ACCENT_PRESSED};
}}
QPushButton:disabled {{
    color: {TEXT_DIM};
    background: {BG_WINDOW};
    border-color: {BORDER};
}}

/* ---- Group boxes ---- */
QGroupBox {{
    background: transparent;
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    background: {BG_WINDOW};
    color: {TEXT};
}}

/* ---- Checkboxes & radios ---- */
QCheckBox, QRadioButton {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    background: {BG_BASE};
    margin-right: 4px;
}}
QCheckBox::indicator {{ border-radius: 3px; }}
QRadioButton::indicator {{ border-radius: 8px; }}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {ACCENT};
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QCheckBox::indicator:checked {{
    image: none;
    /* checkmark via border trick */
    border: 2px solid {BG_BASE};
    background: {ACCENT};
}}

/* ---- Status bar ---- */
QStatusBar {{
    background: {BG_WINDOW};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
    padding: 2px 8px;
}}
QStatusBar::item {{ border: none; }}

/* ---- Tooltips ---- */
QToolTip {{
    background: {BG_BASE};
    color: {TEXT};
    border: 1px solid {ACCENT};
    border-radius: 4px;
    padding: 4px 8px;
}}

/* ---- Tab widget ---- */
QTabWidget::pane {{
    background: {BG_BASE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    top: -1px;
}}
QTabBar::tab {{
    background: {BG_BUTTON};
    color: {TEXT_DIM};
    border: 1px solid {BORDER};
    border-bottom: none;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    min-width: 60px;
}}
QTabBar::tab:selected {{
    background: {BG_BASE};
    color: {TEXT};
    border-bottom: 1px solid {BG_BASE};
}}
QTabBar::tab:hover:!selected {{
    background: {BG_BUTTON_HOVER};
    color: {TEXT};
}}

/* ---- Progress bar ---- */
QProgressBar {{
    background: {BG_BASE};
    border: 1px solid {BORDER};
    border-radius: 4px;
    text-align: center;
    color: {TEXT};
    min-height: 18px;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 3px;
}}

/* ---- Scroll area ---- */
QScrollArea {{
    background: {BG_BASE};
    border: 1px solid {BORDER};
    border-radius: 6px;
}}
"""


def dark_palette() -> QPalette:
    """Build the dark QPalette used across the app."""
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(BG_WINDOW))
    p.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    p.setColor(QPalette.ColorRole.Base, QColor(BG_BASE))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(BG_ALT))
    p.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    p.setColor(QPalette.ColorRole.Button, QColor(BG_BUTTON))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    p.setColor(QPalette.ColorRole.BrightText, QColor(TEXT_BRIGHT))
    p.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(TEXT_BRIGHT))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(BG_BASE))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
    p.setColor(QPalette.ColorRole.Link, QColor(ACCENT_HOVER))
    p.setColor(QPalette.ColorRole.LinkVisited, QColor("#a78bfa"))

    # Disabled state.
    disabled_text = QColor(TEXT_DIM)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_text)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)
    return p


def apply_theme(app: QApplication) -> None:
    """Apply the dark theme to the given QApplication."""
    app.setStyle("Fusion")
    app.setPalette(dark_palette())
    app.setStyleSheet(_QSS)


def refresh_theme() -> None:
    """Re-apply the theme to all top-level widgets."""
    app = QApplication.instance()
    if app is None:
        return
    apply_theme(app)
    for w in app.topLevelWidgets():
        if isinstance(w, QWidget):
            w.setPalette(app.palette())
