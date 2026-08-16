"""Reports dialog — choose and generate a PDF report."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import exporters


class ReportsDialog(QDialog):
    """Generate a PDF inventory report."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("ThingKeeper — Generate report")
        self.setMinimumWidth(460)

        title = QLabel("Generate PDF report")
        title.setStyleSheet("font-weight:bold; font-size:13px;")
        desc = QLabel(
            "Produces a single PDF with: summary, breakdown by group, "
            "and warranty alerts (expired + expiring soon)."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#666;")

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Output .pdf path…")
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse_btn)
        path_widget = QWidget()
        path_widget.setLayout(path_row)

        form = QFormLayout()
        form.addRow("Save to:", path_widget)

        self.generate_btn = QPushButton("Generate")
        self.generate_btn.clicked.connect(self._generate)
        self.generate_btn.setDefault(True)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.generate_btn)
        actions.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addLayout(form)
        layout.addLayout(actions)

        from datetime import date
        default = Path.home() / f"ThingKeeper_Report_{date.today():%Y%m%d}.pdf"
        self.path_edit.setText(str(default))

    def _browse(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save report", self.path_edit.text() or "", "PDF (*.pdf)"
        )
        if path:
            self.path_edit.setText(path)

    def _generate(self) -> None:
        target = self.path_edit.text().strip()
        if not target:
            QMessageBox.warning(self, "Report", "Please choose an output path.")
            return
        if not target.lower().endswith(".pdf"):
            target += ".pdf"
        try:
            exporters.export_pdf_report(target)
        except Exception as exc:  # pragma: no cover - defensive
            QMessageBox.critical(self, "Report", f"Failed to generate report:\n{exc}")
            return
        QMessageBox.information(
            self, "Report",
            f"Report saved to:\n{target}",
        )
        self.accept()
