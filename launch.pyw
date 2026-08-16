#!/usr/bin/env pythonw
"""ThingKeeper launcher - runs the app without a console window.

On Windows, the .pyw extension uses pythonw.exe so no terminal appears.
Double-click launch.bat (preferred) or this file to launch ThingKeeper.

If the app fails to start, check launch_error.log next to this file.
"""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

# Ensure the script's own directory is on sys.path so `import thingkeeper`
# works even when launched via double-click from a different cwd.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# Switch to the script directory so relative data paths resolve correctly.
os.chdir(_HERE)


def main() -> int:
    try:
        from thingkeeper.app import run
        return run()
    except Exception:
        log = _HERE / "launch_error.log"
        with open(log, "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        raise


if __name__ == "__main__":
    raise SystemExit(main())
