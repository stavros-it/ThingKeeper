#!/usr/bin/env python3
"""ThingKeeper launcher - runs the app without a console window.

On Windows, the .pyw extension uses pythonw.exe so no terminal appears.
Double-click this file (or launch.bat) to start ThingKeeper.

Because pythonw.exe disconnects stdout/stderr, diagnostics are redirected
to ``thingkeeper.log`` in the working directory; fatal startup errors are
also shown in a message box. Set ``THINGKEEPER_DEBUG=1`` for verbose logging.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Ensure the script's own directory is on sys.path so `import thingkeeper`
# works even when launched via double-click from a different cwd.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# Switch to the script directory so relative data paths resolve correctly.
os.chdir(_HERE)


def _redirect_streams() -> Path:
    """Redirect stdout/stderr to a log file when running under pythonw.exe.

    Under ``pythonw.exe`` both streams are ``None``; writing to them raises
    "Bad file descriptor". We point them at a log file so tracebacks survive.
    When launched from a terminal (``python.exe``), the real streams are kept.
    """
    log_path = _HERE / "thingkeeper.log"
    try:
        stream = log_path.open("a", encoding="utf-8")
    except OSError:
        stream = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115 - keep open
        log_path = Path(os.devnull)
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream
    return log_path


def _setup_logging() -> None:
    level = logging.DEBUG if os.getenv("THINGKEEPER_DEBUG") else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )


def _show_fatal_error(exc: BaseException, log_path: Path) -> None:
    """Show a message box for a fatal startup error, if Qt is importable."""
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox

        QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "ThingKeeper failed to start",
            f"{type(exc).__name__}: {exc}\n\n"
            f"Diagnostics written to:\n{log_path.resolve()}",
        )
    except Exception:  # noqa: BLE001 - nothing more we can do without Qt
        if sys.stderr:
            sys.stderr.write(
                f"ThingKeeper fatal error: {exc}\n"
                f"Diagnostics: {log_path.resolve()}\n"
            )


def main() -> int:
    log_path = _redirect_streams()
    _setup_logging()
    log = logging.getLogger("launcher")

    try:
        from thingkeeper.app import run

        return run()
    except Exception as exc:  # surface any startup failure to the user
        log.exception("Fatal error during startup")
        _show_fatal_error(exc, log_path)
        return 1


if __name__ == "__main__":
    sys.exit(main())
