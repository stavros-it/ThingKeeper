"""Chart widgets: bar chart (pyqtgraph) and pie chart (QPainter)."""

from __future__ import annotations

import math

import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

pg.setConfigOption("background", "white")
pg.setConfigOption("foreground", "#333333")

_PALETTE = [
    "#305496", "#5b9bd5", "#70ad47", "#ffc000", "#ed7d31",
    "#264478", "#9e480e", "#636363", "#997300", "#43682b",
    "#a5a5a5", "#264653", "#2a9d8f", "#e9c46a", "#f4a261",
]


class BarChartWidget(pg.PlotWidget):
    """Bar chart for counts or values by category."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseEnabled(False, False)
        self.hideButtons()
        self.showGrid(x=False, y=True, alpha=0.3)

    def set_data(self, title: str, labels: list[str], values: list[float]) -> None:
        self.clear()
        if not values:
            self.setTitle(f"{title} — no data")
            return
        self.setTitle(title)
        bg = pg.BarGraphItem(
            x=list(range(len(values))),
            height=values,
            width=0.6,
            brush=QColor("#305496"),
        )
        self.addItem(bg)
        ax = self.getAxis("bottom")
        ax.setTicks([[(i, lbl) for i, lbl in enumerate(labels)]])
        self.getAxis("left").setLabel("Count")


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
        painter.setBrush(QColor("white"))
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
            painter.setPen(QColor("#333333"))
            pct = (self._values[i] / total) * 100 if total else 0
            text = f"{label} ({pct:.0f}%)" if len(label) < 20 else f"{label[:17]}… ({pct:.0f}%)"
            painter.drawText(x + 16, y, 200, line_h, Qt.AlignmentFlag.AlignVCenter, text)

        painter.end()
