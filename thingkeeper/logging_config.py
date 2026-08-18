"""Logging and crash reporting.

Sets up a RotatingFileHandler that writes to ``thingkeeper.log`` in the
data directory, and installs a ``sys.excepthook`` so unhandled exceptions
are captured with a full traceback before the app dies.

Usage (at the very top of the entry point, before any Qt imports)::

    from thingkeeper.logging_config import setup_logging
    setup_logging()
"""

from __future__ import annotations

import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import config

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_FILE: Path = config.DATA_DIR / "thingkeeper.log"

_installed = False


def setup_logging() -> None:
    """Configure root logging with a rotating file handler and excepthook.

    Safe to call multiple times — only the first call has effect.
    """
    global _installed
    if _installed:
        return

    level = logging.DEBUG if _debug_env() else logging.INFO

    try:
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=512 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))

        root = logging.getLogger()
        root.setLevel(level)
        root.addHandler(handler)

        if sys.stderr is not None:
            console = logging.StreamHandler(sys.stderr)
            console.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
            root.addHandler(console)

        sys.excepthook = _excepthook
        _installed = True

        logging.getLogger(__name__).info(
            "ThingKeeper %s starting (log: %s)", config.APP_VERSION, LOG_FILE,
        )
    except Exception:
        _installed = False
        raise


def _debug_env() -> bool:
    import os
    return bool(os.environ.get("THINGKEEPER_DEBUG"))


def _excepthook(exc_type, exc_value, exc_tb) -> None:
    """Log unhandled exceptions before delegating to the default hook."""
    log = logging.getLogger("thingkeeper.crash")
    log.critical(
        "Unhandled exception:\n%s",
        "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
    )
    sys.__excepthook__(exc_type, exc_value, exc_tb)
