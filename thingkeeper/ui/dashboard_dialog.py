"""Dashboard dialog — metric cards and custom bar charts (dark theme).

Redesigned to follow the Game DB stats dialog pattern:
- Metric cards: framed widgets with a big number and label
- Sections: titled framed containers wrapping each chart
- Custom QPainter horizontal bar charts (no pyqtgraph axis issues)
- Scrollable grid of distribution sections
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..repository import (
    all_items,
    counts_by,
    distinct_values,
    qty_by_group,
    total_depreciated_value,
    total_quantity,
    total_value,
    value_by_group,
)
from .charts import BarChart, PieChartWidget
from .theme import ACCENT, BG_BASE, BG_BUTTON, BORDER, INFO, SUCCESS, TEXT, TEXT_DIM

_GRID_COLUMNS = 2


def _metric_card(value: str, label: str, accent: str = ACCENT) -> QFrame:
    card = QFrame()
    card.setObjectName("statCard")
    card.setStyleSheet(f"""
        #statCard {{
            background-color: {BG_BUTTON};
            border: 1px solid {BORDER};
            border-left: 4px solid {accent};
            border-radius: 6px;
        }}
    """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 8, 12, 8)
    layout.setSpacing(2)

    value_lbl = QLabel(str(value))
    font = QFont()
    font.setPointSize(16)
    font.setBold(True)
    value_lbl.setFont(font)
    value_lbl.setStyleSheet(f"color: {accent}; background: transparent; border: none;")
    value_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.addWidget(value_lbl)

    label_lbl = QLabel(label)
    small = QFont()
    small.setPointSize(8)
    label_lbl.setFont(small)
    label_lbl.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
    label_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.addWidget(label_lbl)
    return card


def _section(title: str, body: QWidget) -> QFrame:
    frame = QFrame()
    frame.setObjectName("section")
    frame.setStyleSheet(f"""
        #section {{
            background-color: {BG_BUTTON};
            border: 1px solid {BORDER};
            border-radius: 8px;
        }}
    """)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 10, 14, 12)
    layout.setSpacing(8)

    title_lbl = QLabel(title)
    font = QFont()
    font.setPointSize(10)
    font.setBold(True)
    title_lbl.setFont(font)
    title_lbl.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
    layout.addWidget(title_lbl)
    layout.addWidget(body, 1)
    return frame


class DashboardDialog(QDialog):
    """Visual overview: metric cards + horizontal bar charts + pie chart."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ThingKeeper - Dashboard")
        self.setMinimumWidth(760)
        self.resize(1000, 800)
        self.setStyleSheet(f"QDialog {{ background-color: {BG_BASE}; }}")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 12)
        outer.setSpacing(12)

        outer.addLayout(self._build_header())
        outer.addLayout(self._build_metric_cards())
        outer.addWidget(self._build_distributions_scroll(), 1)

        actions = QHBoxLayout()
        actions.addStretch(1)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        actions.addWidget(refresh_btn)
        actions.addWidget(close_btn)
        outer.addLayout(actions)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        header.addWidget(title)
        header.addStretch()

        items = all_items()
        total_lbl = QLabel(f"{len(items):,} items")
        total_font = QFont()
        total_font.setPointSize(12)
        total_font.setBold(True)
        total_lbl.setFont(total_font)
        total_lbl.setStyleSheet(f"color: {INFO}; background: transparent;")
        header.addWidget(total_lbl)
        return header

    def _build_metric_cards(self) -> QHBoxLayout:
        items = all_items()
        tval = total_value()
        dval = total_depreciated_value()
        cards_row = QHBoxLayout()
        cards_row.setSpacing(8)
        cards = [
            (str(len(items)), "Items", ACCENT),
            (str(total_quantity()), "Total qty", INFO),
            (str(len(distinct_values("group_name"))), "Groups", SUCCESS),
            (f"{tval:,.0f}", "Purchase value", "#fbbf24"),
            (f"{dval:,.0f}", "Depreciated", "#f87171"),
        ]
        for value, label, accent in cards:
            cards_row.addWidget(_metric_card(value, label, accent))
        cards_row.addStretch()
        return cards_row

    def _build_distributions_scroll(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        grid = QGridLayout(scroll_content)
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        self._sections: list[tuple[str, str, bool, str]] = []
        self._scroll_grid = grid
        self._scroll_content = scroll_content

        scroll.setWidget(scroll_content)
        return scroll

    def _place_sections(self, sections: list[tuple[str, QWidget]]) -> None:
        grid = self._scroll_grid
        for idx, (title, widget) in enumerate(sections):
            row = idx // _GRID_COLUMNS
            col = idx % _GRID_COLUMNS
            is_last = idx == len(sections) - 1
            if is_last and col != 0:
                grid.addWidget(_section(title, widget), row, 0, 1, _GRID_COLUMNS)
            else:
                grid.addWidget(_section(title, widget), row, col)

    def refresh(self) -> None:
        for i in reversed(range(self._scroll_grid.count())):
            item = self._scroll_grid.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        sections: list[tuple[str, QWidget]] = []

        qg = qty_by_group()
        if qg:
            chart = BarChart(qg, color=ACCENT)
            chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            sections.append(("Items by group", chart))

        sc = counts_by("status")
        if sc:
            pie = PieChartWidget()
            pie.set_data(
                "Status distribution",
                [s for s, _ in sc],
                [float(v) for _, v in sc],
            )
            sections.append(("Status distribution", pie))

        vg = value_by_group()
        if vg:
            chart = BarChart(vg, color=INFO, value_format="{:,.0f}")
            chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            sections.append(("Value by group", chart))

        cg = counts_by("type")
        if cg:
            cg_sorted = sorted(cg, key=lambda x: x[1], reverse=True)[:15]
            chart = BarChart(cg_sorted, color=SUCCESS)
            chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            sections.append(("Items by type (top 15)", chart))

        bg = counts_by("brand")
        if bg:
            bg_sorted = sorted(bg, key=lambda x: x[1], reverse=True)[:15]
            chart = BarChart(bg_sorted, color="#fbbf24")
            chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            sections.append(("Items by brand (top 15)", chart))

        self._place_sections(sections)
