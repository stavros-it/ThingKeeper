"""App bootstrap: initialise the database and launch the Qt UI."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from . import config
from .database import init_db
from .ui.main_window import MainWindow
from .ui.theme import apply_theme

_ICON_PATH = Path(__file__).resolve().parent / "assets" / "app.ico"


def _set_app_user_model_id() -> None:
    """On Windows, set the AppUserModelID so the taskbar groups correctly."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                f"{config.APP_NAME}.App"
            )
        except (OSError, AttributeError):
            pass


def run() -> int:
    _set_app_user_model_id()
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setOrganizationName(config.APP_NAME)
    if _ICON_PATH.is_file():
        app.setWindowIcon(QIcon(str(_ICON_PATH)))
    apply_theme(app)
    window = MainWindow()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
