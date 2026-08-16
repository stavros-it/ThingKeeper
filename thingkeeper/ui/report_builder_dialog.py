"""Custom report builder — choose columns, filters, grouping, sort, generate PDF."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..repository import Item, distinct_values

# All exportable columns: (label, attribute, is_numeric).
ALL_COLUMNS = [
    ("ID", "id", True),
    ("Group", "group_name", False),
    ("Type", "type", False),
    ("Brand", "brand", False),
    ("Model", "model", False),
    ("Serial", "serial", False),
    ("Status", "status", False),
    ("Quantity", "quantity", True),
    ("Location", "location", False),
    ("Purchase date", "purchase_date", False),
    ("Warranty end", "warranty_end", False),
    ("Store", "store", False),
    ("Unit price", "unit_price", True),
    ("Depreciation years", "depreciation_years", True),
]


class ReportBuilderDialog(QDialog):
    """Build a custom PDF report from chosen columns, filters and grouping."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("ThingKeeper — Custom report")
        self.setMinimumWidth(560)

        # Column selection.
        cols_box = QGroupBox("Columns")
        cols_layout = QHBoxLayout(cols_box)
        self.col_checks: list[tuple[str, str, QCheckBox]] = []
        for label, attr, _ in ALL_COLUMNS:
            cb = QCheckBox(label)
            cb.setChecked(True)
            self.col_checks.append((label, attr, cb))
            cols_layout.addWidget(cb)
        cols_layout.addStretch(1)

        # Filters.
        filters_box = QGroupBox("Filters")
        filters_layout = QFormLayout(filters_box)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Text search…")
        self.group_combo = self._filter_combo("group_name")
        self.status_combo = QComboBox()
        self.status_combo.addItem("(all)", "")
        for s in distinct_values("status"):
            self.status_combo.addItem(s, s)
        filters_layout.addRow("Search:", self.search_edit)
        filters_layout.addRow("Group:", self.group_combo)
        filters_layout.addRow("Status:", self.status_combo)

        # Grouping + sort.
        options_box = QGroupBox("Grouping & sort")
        options_layout = QFormLayout(options_box)
        self.group_by_combo = QComboBox()
        self.group_by_combo.addItem("(none)", "")
        for label, attr, _ in ALL_COLUMNS:
            self.group_by_combo.addItem(label, attr)
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.addItem("(none)", "")
        for label, attr, is_num in ALL_COLUMNS:
            self.sort_by_combo.addItem(f"{label} (asc)", (attr, is_num, False))
            self.sort_by_combo.addItem(f"{label} (desc)", (attr, is_num, True))
        options_layout.addRow("Group by:", self.group_by_combo)
        options_layout.addRow("Sort by:", self.sort_by_combo)

        # Output path.
        path_box = QGroupBox("Output")
        path_layout = QHBoxLayout(path_box)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Output .pdf path…")
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        path_layout.addWidget(self.path_edit, 1)
        path_layout.addWidget(browse_btn)

        from datetime import date
        default = Path.home() / f"ThingKeeper_Custom_{date.today():%Y%m%d}.pdf"
        self.path_edit.setText(str(default))

        generate_btn = QPushButton("Generate")
        generate_btn.setDefault(True)
        generate_btn.clicked.connect(self._generate)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(generate_btn)
        actions.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(cols_box)
        layout.addWidget(filters_box)
        layout.addWidget(options_box)
        layout.addWidget(path_box)
        layout.addLayout(actions)

    def _filter_combo(self, column: str) -> QComboBox:
        combo = QComboBox()
        combo.addItem("(all)", "")
        combo.addItems(distinct_values(column))
        return combo

    def _browse(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save report", self.path_edit.text() or "", "PDF (*.pdf)"
        )
        if path:
            self.path_edit.setText(path)

    def _selected_columns(self) -> list[tuple[str, str]]:
        return [(label, attr) for label, attr, cb in self.col_checks if cb.isChecked()]

    def _filtered_items(self) -> list[Item]:
        from ..repository import list_items

        return list_items(
            search=self.search_edit.text().strip(),
            group=self.group_combo.currentData(),
            status=self.status_combo.currentData(),
        )

    def _generate(self) -> None:
        target = self.path_edit.text().strip()
        if not target:
            QMessageBox.warning(self, "Report", "Please choose an output path.")
            return
        if not target.lower().endswith(".pdf"):
            target += ".pdf"
        cols = self._selected_columns()
        if not cols:
            QMessageBox.warning(self, "Report", "Select at least one column.")
            return

        items = self._filtered_items()

        # Sort.
        sort_data = self.sort_by_combo.currentData()
        if sort_data:
            attr, is_num, desc = sort_data
            items.sort(
                key=lambda it: (getattr(it, attr, "") or (0 if is_num else "")),
                reverse=desc,
            )

        group_attr = self.group_by_combo.currentData()

        try:
            self._build_pdf(target, items, cols, group_attr)
        except Exception as exc:  # pragma: no cover - defensive
            QMessageBox.critical(self, "Report", f"Failed to generate:\n{exc}")
            return
        QMessageBox.information(self, "Report", f"Report saved to:\n{target}")
        self.accept()

    def _build_pdf(
        self,
        path: str,
        items: list[Item],
        cols: list[tuple[str, str]],
        group_attr: str,
    ) -> None:
        from datetime import datetime as dt

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
        )

        doc = SimpleDocTemplate(
            path, pagesize=landscape(A4),
            leftMargin=12 * mm, rightMargin=12 * mm,
            topMargin=12 * mm, bottomMargin=12 * mm,
        )
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("<b>ThingKeeper Custom Report</b>", styles["Title"]))
        stamp = dt.now().strftime("%Y-%m-%d %H:%M")
        story.append(Paragraph(
            f"{len(items)} items - generated {stamp}",
            styles["Normal"],
        ))
        story.append(Spacer(1, 6 * mm))

        if group_attr:
            self._grouped_tables(story, items, cols, group_attr, styles, colors)
        else:
            self._single_table(story, items, cols, colors)

        doc.build(story)

    def _single_table(self, story, items, cols, colors_) -> None:
        from reportlab.platypus import Table, TableStyle

        headers = [label for label, _ in cols]
        data = [headers]
        for it in items:
            row = [str(getattr(it, attr, "") or "") for _, attr in cols]
            data.append(row)
        col_w = [180 * 0.5] * len(cols)
        tbl = Table(data, colWidths=col_w, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors_.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors_.HexColor("#305496")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors_.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(tbl)

    def _grouped_tables(self, story, items, cols, group_attr, styles, colors_) -> None:
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

        groups: dict[str, list[Item]] = {}
        for it in items:
            key = str(getattr(it, group_attr, "") or "(none)")
            groups.setdefault(key, []).append(it)
        headers = [label for label, _ in cols]
        for key in sorted(groups):
            story.append(Paragraph(
                f"<b>{key}</b> ({len(groups[key])} items)",
                styles["Heading3"],
            ))
            data = [headers]
            for it in groups[key]:
                row = [str(getattr(it, attr, "") or "") for _, attr in cols]
                data.append(row)
            col_w = [180 * 0.5] * len(cols)
            tbl = Table(data, colWidths=col_w, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors_.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors_.HexColor("#5b9bd5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors_.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 4 * mm))
