#!/usr/bin/env pythonw
"""ThingKeeper launcher — runs the app without a console window.

On Windows, the .pyw extension uses pythonw.exe so no terminal appears.
Double-click this file (or pin it to the taskbar) to launch ThingKeeper.
"""

from thingkeeper.app import run

if __name__ == "__main__":
    raise SystemExit(run())
