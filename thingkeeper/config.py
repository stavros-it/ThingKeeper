"""Application paths and shared constants."""

from __future__ import annotations

import os
from pathlib import Path

# Project root (one level up from this package).
APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent

# Runtime data lives in ./data — git-ignored so user inventory stays local.
DATA_DIR = Path(os.environ.get("THINGKEEPER_DATA", ROOT_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "thingkeeper.db"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "ThingKeeper"
APP_VERSION = "0.2.0"

# Status lifecycle.
STATUSES = ["AVAILABLE", "IN USE", "LOANED", "BROKEN", "SOLD"]
DEFAULT_STATUS = "AVAILABLE"

# Archive extension for compressed JSON backups (with attachments).
ARCHIVE_EXT = ".tkz"

# How many days before warranty end counts as "expiring soon".
WARRANTY_SOON_DAYS = 30
