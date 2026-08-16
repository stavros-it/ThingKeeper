"""Allow `python -m thingkeeper` to launch the app or generate a scheduled report.

Usage:
    python -m thingkeeper                  # launch the GUI
    python -m thingkeeper --report PATH    # generate a PDF report to PATH
"""

from __future__ import annotations

import argparse


def run() -> int:
    parser = argparse.ArgumentParser(
        prog="thingkeeper",
        description="ThingKeeper desktop inventory app.",
    )
    parser.add_argument(
        "--report",
        metavar="PATH",
        help="Generate a PDF inventory report to PATH and exit (no GUI).",
    )
    args = parser.parse_args()

    if args.report:
        from .database import init_db
        from .exporters import export_pdf_report

        init_db()
        export_pdf_report(args.report)
        print(f"Report saved to {args.report}")
        return 0

    from .app import run as run_gui

    return run_gui()


if __name__ == "__main__":
    raise SystemExit(run())
