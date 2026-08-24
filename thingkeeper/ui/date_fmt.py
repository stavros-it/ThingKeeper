"""Regional date formatting helpers.

Dates are stored as ISO ``YYYY-MM-DD`` text in SQLite for portability and
sortability. For display we render them with the host operating system's
short date format via ``QLocale.system()`` so users see what they expect
in dialogs and the items table.

This module is the only place that knows about ``QLocale``; UI code calls
``qt_date_format()`` for ``QDateEdit`` widgets and ``format_iso_date()`` for
plain string rendering. Storage is always ISO and is never mutated.
"""

from __future__ import annotations

from datetime import date

_FALLBACK_QT_FORMAT = "yyyy-MM-dd"


def qt_date_format() -> str:
    """Return the OS regional short date format in Qt ``QDateEdit`` syntax.

    Falls back to ``yyyy-MM-dd`` when Qt is unavailable (e.g. headless
    imports that never touch the UI layer).
    """
    try:
        from PyQt6.QtCore import QLocale
    except ImportError:
        return _FALLBACK_QT_FORMAT
    fmt = QLocale.system().dateFormat(QLocale.FormatType.ShortFormat)
    return fmt or _FALLBACK_QT_FORMAT


def format_iso_date(iso: str) -> str:
    """Render an ISO ``YYYY-MM-DD`` date using the OS regional short format.

    Returns the input unchanged on any parse failure or empty input, so
    malformed values never crash the UI.
    """
    if not iso or len(iso) < 10:
        return iso
    try:
        y, m, d = iso[:10].split("-")
        dt = date(int(y), int(m), int(d))
    except ValueError:
        return iso
    try:
        from PyQt6.QtCore import QLocale
    except ImportError:
        return iso
    return QLocale.system().toString(dt, QLocale.FormatType.ShortFormat)
