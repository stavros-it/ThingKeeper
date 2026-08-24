"""Window sizing helpers that respect the available desktop area.

``availableGeometry()`` on a ``QScreen`` returns the screen region not
occupied by the taskbar (Windows) or panels (Linux/X11 WMs).  These
helpers size a top-level widget to a fraction of that region and centre
it, so dialogs fill the vertical space from the top of the work area
down to the top of the taskbar.
"""

from __future__ import annotations

from PyQt6.QtWidgets import QApplication, QWidget


def size_to_available(
    widget: QWidget,
    w_ratio: float,
    h_ratio: float,
    max_w: int | None = None,
) -> None:
    """Resize ``widget`` to a fraction of the available screen area.

    ``w_ratio`` and ``h_ratio`` are clamped to ``[0.0, 1.0]``.  If
    ``max_w`` is given, the width is capped to that many pixels so the
    window does not look excessively wide on large monitors.  The widget
    is centred within the available geometry of its current screen (or
    the primary screen if it has none yet).  Falls back silently when
    no screen is available (headless tests).
    """
    screen = widget.screen() if hasattr(widget, "screen") else None
    if screen is None:
        app = QApplication.instance()
        if app is not None:
            screen = app.primaryScreen()
    if screen is None:
        return

    avail = screen.availableGeometry()
    w = int(avail.width() * max(0.0, min(1.0, w_ratio)))
    if max_w is not None:
        w = min(w, max_w)
    h = int(avail.height() * max(0.0, min(1.0, h_ratio)))
    widget.resize(w, h)
    widget.move(
        avail.x() + (avail.width() - w) // 2,
        avail.y() + (avail.height() - h) // 2,
    )
