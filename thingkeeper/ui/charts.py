"""Chart widgets: bar chart (pyqtgraph) and pie chart (QPainter)."""

from __future__ import annotations

import math

import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from .theme import ACCENT, BG_WINDOW, TEXT

pg.setConfigOption("background", BG_WINDOW)
pg.setConfigOption("foreground", TEXT)

_PALETTE = [
    "#3b82f6", "#60a5fa", "#4ade80", "#fbbf24", "#f87171",
    "#a78bfa", "#22d3ee", "#fb923c", "#94a3b8", "#facc15",
    "#34d399", "#264653", "#2a9d8f", "#e9c46a", "#f4a261",
]


class BarChartWidget(pg.PlotWidget):
    """Bar chart for counts or values by category."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseEnabled(False, False)
        self.hideButtons()
        self.showGrid(x=False, y=True, alpha=0.25)

    def set_data(self, title: str, labels: list[str], values: list[float]) -> None:
        self.clear()
        if not values:
            self.setTitle(f"{title} - no data")
            return
        self.setTitle(title)
        bg = pg.BarGraphItem(
            x=list(range(len(values))),
            height=values,
            width=0.6,
            brush=QColor(ACCENT),
        )
        self.addItem(bg)
        ax = self.getAxis("bottom")
        ax.setTicks([[(i, "") for i in range(len(labels))]])
        ax.setStyle(showValues=False)
        self.getAxis("left").setLabel("Count")
        max_val = max(values) if values else 0
        for i, lbl in enumerate(labels):
            txt = pg.TextItem(lbl, color=TEXT, anchor=(1, 0))
            txt.setFont(QFont("Segoe UI", 9))
            txt.setAngle(-45)
            txt.setPos(i, -0.02 * max_val)
            self.addItem(txt)
        bottom = self.getAxis("bottom")
        bottom.setStyle(tickLength=0)


class PieChartWidget(QWidget):
    """Simple pie/donut chart drawn with QPainter."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._labels: list[str] = []
        self._values: list[float] = []
        self._title: str = ""
        self.setMinimumSize(300, 300)

    def set_data(self, title: str, labels: list[str], values: list[float]) -> None:
        self._title = title
        self._labels = labels
        self._values = values
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        total = sum(self._values)
        cx, cy = w // 2, h // 2 - 10
        radius = min(w, h) * 0.35

        # Title.
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        title_text = self._title if total > 0 else f"{self._title} — no data"
        painter.drawText(0, 0, w, 28, Qt.AlignmentFlag.AlignCenter, title_text)

        if total == 0:
            painter.end()
            return

        # Pie slices.
        angle = 90.0
        for i, val in enumerate(self._values):
            span = (val / total) * 360.0
            color = QColor(_PALETTE[i % len(_PALETTE)])
            painter.setBrush(color)
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawPie(
                cx - radius, cy - radius, int(radius * 2), int(radius * 2),
                int(angle * 16), int(-span * 16),
            )
            angle -= span

        # Donut hole.
        painter.setBrush(QColor(BG_WINDOW))
        painter.drawEllipse(
            int(cx - radius * 0.45), int(cy - radius * 0.45),
            int(radius * 0.9), int(radius * 0.9),
        )

        # Legend.
        font.setPointSize(9)
        font.setBold(False)
        painter.setFont(font)
        legend_y = cy + int(radius) + 15
        line_h = 16
        cols = max(1, math.ceil(len(self._labels) / 4))
        per_col = math.ceil(len(self._labels) / cols)
        for i, label in enumerate(self._labels):
            col = i // per_col
            row = i % per_col
            x = col * (w // cols) + 10
            y = legend_y + row * line_h
            if y > h - line_h:
                continue
            painter.setBrush(QColor(_PALETTE[i % len(_PALETTE)]))
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawRect(x, y + 2, 10, 10)
            painter.setPen(QColor(TEXT))
            pct = (self._values[i] / total) * 100 if total else 0
            text = f"{label} ({pct:.0f}%)" if len(label) < 20 else f"{label[:17]}… ({pct:.0f}%)"
            painter.drawText(x + 16, y, 200, line_h, Qt.AlignmentFlag.AlignVCenter, text)

        painter.end()
