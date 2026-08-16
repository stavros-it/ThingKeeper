"""Chart widgets: custom QPainter bar chart and pie chart.

No pyqtgraph dependency for the bar chart — we draw it ourselves with
QPainter, which gives full control over label placement and avoids the
axis-clipping issues that plagued the pyqtgraph-based version.

The design follows the Game DB stats dialog pattern:
- Horizontal bars with a track (full width) + fill (proportional)
- Smart in-bar labels (label left, value right) with contrast-aware text color
- Rounded corners, expand to fill available space
"""

from __future__ import annotations

import math

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from .theme import (
    ACCENT,
    BG_WINDOW,
    BORDER,
    STATUS_COLORS,
    TEXT,
    TEXT_BRIGHT,
    TEXT_DIM,
)

_PALETTE = [
    "#3b82f6", "#60a5fa", "#4ade80", "#fbbf24", "#f87171",
    "#a78bfa", "#22d3ee", "#fb923c", "#94a3b8", "#facc15",
    "#34d399", "#264653", "#2a9d8f", "#e9c46a", "#f4a261",
]


def _luminance(hex_color: str) -> float:
    c = QColor(hex_color)
    if not c.isValid():
        return 0.0

    def ch(v: int) -> float:
        s = v / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    return 0.2126 * ch(c.red()) + 0.7152 * ch(c.green()) + 0.0722 * ch(c.blue())


def _contrast_text(bg_hex: str) -> QColor:
    return QColor("#0F172A") if _luminance(bg_hex) > 0.20 else QColor(TEXT_BRIGHT)


class BarChart(QWidget):
    """Horizontal bar chart with in-bar labels and numbers.

    Bars fill available vertical space evenly. Text color inside each bar
    is chosen by luminance: white on dark fills, near-black on light fills.
    """

    def __init__(
        self,
        data: list[tuple[str, int | float]],
        color: str = ACCENT,
        *,
        use_status_colors: bool = False,
        value_format: str = "{:.0f}",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._data = data
        self._color = color
        self._use_status_colors = use_status_colors
        self._value_format = value_format
        self._min_bar_h = 22
        self._max_bar_h = 32
        self._gap = 4
        rows = max(len(data), 1)
        capped_rows = min(rows, 20)
        self.setMinimumHeight(capped_rows * (self._min_bar_h + self._gap) + 4)
        self.setMinimumWidth(320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data: list[tuple[str, int | float]]) -> None:
        self._data = data
        rows = max(len(data), 1)
        self.setMinimumHeight(rows * (self._min_bar_h + self._gap) + 4)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt override
        if not self._data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        max_val = max((v for _, v in self._data), default=1) or 1
        w = self.width()
        h = self.height()
        n = len(self._data)

        gap = self._gap
        bar_h = min(self._max_bar_h, (h - gap * (n - 1) - 4) // n) if n > 0 else self._min_bar_h
        bar_h = max(bar_h, self._min_bar_h)
        total_h = bar_h * n + gap * (n - 1)
        y_start = (h - total_h) // 2
        pad = 10

        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        fm = painter.fontMetrics()

        text_muted = QColor(TEXT_DIM)
        track_color = QColor(BORDER)

        for i, (label, value) in enumerate(self._data):
            y = y_start + i * (bar_h + gap)
            fill_w = int(w * value / max_val) if max_val else 0

            painter.setBrush(track_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(0, y, w, bar_h, 4, 4)

            fill_color_hex = self._color
            if fill_w > 0:
                if self._use_status_colors:
                    fill_color_hex = STATUS_COLORS.get(label, self._color)
                painter.setBrush(QColor(fill_color_hex))
                painter.drawRoundedRect(0, y, fill_w, bar_h, 4, 4)

            in_bar_text = _contrast_text(fill_color_hex) if fill_w > 0 else text_muted

            value_text = self._value_format.format(value)
            label_w = fm.horizontalAdvance(label)
            value_w = fm.horizontalAdvance(value_text)

            both_fit = fill_w >= label_w + value_w + pad * 3
            value_fits = fill_w >= value_w + pad * 2

            if fill_w > 0 and both_fit:
                painter.setPen(in_bar_text)
                painter.drawText(
                    pad, y, fill_w - pad * 2 - value_w, bar_h,
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label,
                )
                painter.drawText(
                    pad, y, fill_w - pad * 2, bar_h,
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, value_text,
                )
            elif fill_w > 0 and value_fits:
                painter.setPen(in_bar_text)
                painter.drawText(
                    pad, y, fill_w - pad * 2, bar_h,
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, value_text,
                )
                painter.setPen(text_muted)
                painter.drawText(
                    fill_w + pad, y, w - fill_w - pad, bar_h,
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label,
                )
            else:
                painter.setPen(text_muted)
                painter.drawText(
                    fill_w + pad, y, w - fill_w - pad, bar_h,
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label,
                )
                painter.drawText(
                    0, y, w - pad, bar_h,
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, value_text,
                )


class PieChartWidget(QWidget):
    """Simple pie/donut chart drawn with QPainter."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._labels: list[str] = []
        self._values: list[float] = []
        self._title: str = ""
        self.setMinimumHeight(250)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, title: str, labels: list[str], values: list[float]) -> None:
        self._title = title
        self._labels = labels
        self._values = values
        self.update()

    def _color_for(self, i: int, label: str) -> str:
        if label in STATUS_COLORS:
            return STATUS_COLORS[label]
        return _PALETTE[i % len(_PALETTE)]

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        total = sum(self._values)
        cx, cy = w // 2, h // 2 - 10
        radius = min(w, h) * 0.35

        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        title_text = self._title if total > 0 else f"{self._title} - no data"
        painter.drawText(0, 0, w, 28, Qt.AlignmentFlag.AlignCenter, title_text)

        if total == 0:
            painter.end()
            return

        angle = 90.0
        for i, val in enumerate(self._values):
            span = (val / total) * 360.0
            color = QColor(self._color_for(i, self._labels[i]))
            painter.setBrush(color)
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawPie(
                int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2),
                int(angle * 16), int(-span * 16),
            )
            angle -= span

        painter.setBrush(QColor(BG_WINDOW))
        painter.drawEllipse(
            int(cx - radius * 0.45), int(cy - radius * 0.45),
            int(radius * 0.9), int(radius * 0.9),
        )

        font.setPointSize(9)
        font.setBold(False)
        painter.setFont(font)
        legend_y = cy + int(radius) + 15
        line_h = 16
        n = len(self._labels)
        cols = max(1, math.ceil(n / 4))
        per_col = math.ceil(n / cols)
        for i, label in enumerate(self._labels):
            col = i // per_col
            row = i % per_col
            x = col * (w // cols) + 10
            y = legend_y + row * line_h
            if y > h - line_h:
                continue
            color_hex = self._color_for(i, label)
            painter.setBrush(QColor(color_hex))
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawRect(x, y + 2, 10, 10)
            painter.setPen(QColor(TEXT))
            pct = (self._values[i] / total) * 100 if total else 0
            text = f"{label} ({pct:.0f}%)" if len(label) < 20 else f"{label[:17]}... ({pct:.0f}%)"
            painter.drawText(x + 16, y, 200, line_h, Qt.AlignmentFlag.AlignVCenter, text)

        painter.end()
