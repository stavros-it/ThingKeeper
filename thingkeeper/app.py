"""App bootstrap: initialise the database and launch the Qt UI."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from . import config
from .database import init_db
from .ui.main_window import MainWindow
from .ui.theme import apply_theme


def run() -> int:
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setOrganizationName("ThingKeeper")
    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
