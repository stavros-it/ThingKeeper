"""Dashboard dialog — charts and summary statistics."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
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
from .charts import BarChartWidget, PieChartWidget


class DashboardDialog(QDialog):
    """Visual overview: bar chart by group, pie by status, value summary."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ThingKeeper — Dashboard")
        self.resize(1400, 1000)
        self.setMinimumSize(1100, 800)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        # Summary stats.
        items = all_items()
        tval = total_value()
        dval = total_depreciated_value()

        stats_box = QGroupBox("Summary")
        stats_layout = QHBoxLayout(stats_box)
        stats = [
            ("Items", str(len(items))),
            ("Total qty", str(total_quantity())),
            ("Groups", str(len(distinct_values("group_name")))),
            ("Purchase value", f"{tval:,.2f}"),
            ("Depreciated value", f"{dval:,.2f}"),
        ]
        for label, value in stats:
            cell = QVBoxLayout()
            v = QLabel(value)
            v.setStyleSheet("font-size: 20px; font-weight: 700;")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 11px; color: #9a9a9a; letter-spacing: 0.5px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell.addWidget(v)
            cell.addWidget(lbl)
            stats_layout.addLayout(cell)
            if label != "Depreciated value":
                stats_layout.addSpacing(20)

        # Charts.
        self.qty_chart = BarChartWidget()
        self.status_chart = PieChartWidget()
        self.value_chart = BarChartWidget()

        charts_grid = QGridLayout()
        charts_grid.setVerticalSpacing(60)
        charts_grid.setHorizontalSpacing(20)
        charts_grid.addWidget(self.qty_chart, 0, 0)
        charts_grid.addWidget(self.status_chart, 0, 1)
        charts_grid.addWidget(self.value_chart, 1, 0, 1, 2)
        charts_grid.setColumnStretch(0, 1)
        charts_grid.setColumnStretch(1, 1)
        charts_grid.setRowStretch(0, 1)
        charts_grid.setRowStretch(1, 1)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(refresh_btn)
        actions.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(stats_box)
        layout.addLayout(charts_grid, 1)
        layout.addLayout(actions)

    def refresh(self) -> None:
        # Quantity by group (bar chart).
        qg = qty_by_group()
        self.qty_chart.set_data(
            "Items by group",
            [g for g, _ in qg],
            [float(v) for _, v in qg],
        )

        # Status distribution (pie chart).
        sc = counts_by("status")
        self.status_chart.set_data(
            "Status distribution",
            [s for s, _ in sc],
            [float(v) for _, v in sc],
        )

        # Value by group (bar chart).
        vg = value_by_group()
        self.value_chart.set_data(
            "Value by group",
            [g for g, _ in vg],
            [v for _, v in vg],
        )
