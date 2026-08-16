"""Add/Edit item dialog with image attachment and warranty support."""

from __future__ import annotations

import shutil
import uuid
from datetime import date
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import config
from ..repository import Item, distinct_values


class ItemDialog(QDialog):
    """Modal dialog for creating or editing an Item."""

    def __init__(self, parent: QWidget | None = None, item: Item | None = None) -> None:
        super().__init__(parent)
        self._item = item
        self._image_path: str = ""
        self._build_ui()
        if item is not None:
            self._load_item(item)

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.setWindowTitle("ThingKeeper — Item")
        self.setMinimumWidth(640)

        self.group_edit = self._combo_edit("group_name")
        self.type_edit = self._combo_edit("type")
        self.brand_edit = self._combo_edit("brand")
        self.model_edit = QLineEdit()
        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("Serial number / barcode")
        self.store_edit = self._combo_edit("store")
        self.location_edit = self._combo_edit("location")

        self.status_combo = QComboBox()
        self.status_combo.addItems(config.STATUSES)

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 1_000_000)
        self.qty_spin.setValue(1)

        self.purchase_edit = QDateEdit()
        self.purchase_edit.setCalendarPopup(True)
        self.purchase_edit.setDisplayFormat("yyyy-MM-dd")
        self.purchase_edit.setDate(date.today())

        self.warranty_edit = QDateEdit()
        self.warranty_edit.setCalendarPopup(True)
        self.warranty_edit.setDisplayFormat("yyyy-MM-dd")
        self.warranty_edit.setDate(date.today())
        self.warranty_check = QCheckBox("Has warranty")
        self.warranty_check.toggled.connect(self._on_warranty_toggled)
        self._on_warranty_toggled(False)

        self.info_edit = QTextEdit()
        self.info_edit.setMaximumHeight(90)

        # Image attachment.
        self.image_label = QLabel("No image")
        self.image_label.setFixedSize(220, 160)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            "QLabel { background:#f4f4f4; border:1px dashed #bbb; border-radius:6px; }"
        )
        self.attach_btn = QPushButton("Choose image…")
        self.attach_btn.clicked.connect(self._choose_image)
        self.clear_img_btn = QPushButton("Remove")
        self.clear_img_btn.clicked.connect(self._clear_image)

        img_row = QHBoxLayout()
        img_row.addWidget(self.image_label)
        img_col = QVBoxLayout()
        img_col.addWidget(self.attach_btn)
        img_col.addWidget(self.clear_img_btn)
        img_col.addStretch(1)
        img_row.addLayout(img_col, 1)
        img_widget = QWidget()
        img_widget.setLayout(img_row)

        warranty_row = QHBoxLayout()
        warranty_row.addWidget(self.warranty_edit, 1)
        warranty_row.addWidget(self.warranty_check)
        warranty_widget = QWidget()
        warranty_widget.setLayout(warranty_row)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.addRow("Group:", self.group_edit)
        form.addRow("Type:", self.type_edit)
        form.addRow("Brand:", self.brand_edit)
        form.addRow("Model:", self.model_edit)
        form.addRow("Serial:", self.serial_edit)
        form.addRow("Status:", self.status_combo)
        form.addRow("Quantity:", self.qty_spin)
        form.addRow("Store:", self.store_edit)
        form.addRow("Location:", self.location_edit)
        form.addRow("Purchase date:", self.purchase_edit)
        form.addRow("Warranty end:", warranty_widget)
        form.addRow("Notes:", self.info_edit)
        form.addRow("Image:", img_widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _combo_edit(self, column: str) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(distinct_values(column))
        return combo

    def _on_warranty_toggled(self, checked: bool) -> None:
        self.warranty_edit.setEnabled(checked)

    # ------------------------------------------------------------- behaviour
    def _load_item(self, item: Item) -> None:
        self.setWindowTitle("ThingKeeper — Edit item")
        self.group_edit.setEditText(item.group_name)
        self.type_edit.setEditText(item.type)
        self.brand_edit.setEditText(item.brand)
        self.model_edit.setText(item.model)
        self.serial_edit.setText(item.serial)
        self.store_edit.setEditText(item.store)
        self.location_edit.setEditText(item.location)
        if item.status in config.STATUSES:
            self.status_combo.setCurrentText(item.status)
        self.qty_spin.setValue(max(1, item.quantity))
        self.purchase_edit.setDate(self._parse_date(item.purchase_date, date.today()))
        if item.warranty_end:
            self.warranty_check.setChecked(True)
            self.warranty_edit.setDate(self._parse_date(item.warranty_end, date.today()))
        self.info_edit.setPlainText(item.info)
        self._image_path = item.image_path
        self._refresh_image_preview()

    @staticmethod
    def _parse_date(value: str, fallback: date) -> date:
        if not value:
            return fallback
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return fallback

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.gif);;All files (*.*)",
        )
        if not path:
            return
        # Copy into the attachments dir with a unique name to avoid collisions.
        ext = Path(path).suffix or ".img"
        target = config.ATTACHMENTS_DIR / f"{uuid.uuid4().hex}{ext}"
        try:
            shutil.copyfile(path, target)
        except OSError as exc:
            QMessageBox.warning(self, "Image", f"Could not copy image:\n{exc}")
            return
        self._image_path = str(target)
        self._refresh_image_preview()

    def _clear_image(self) -> None:
        self._image_path = ""
        self._refresh_image_preview()

    def _refresh_image_preview(self) -> None:
        if self._image_path and Path(self._image_path).exists():
            pix = QPixmap(self._image_path)
            if not pix.isNull():
                self.image_label.setPixmap(
                    pix.scaled(
                        self.image_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                return
        self.image_label.setText("No image")
        self.image_label.setPixmap(QPixmap())

    def _validate_and_accept(self) -> None:
        if not self.model_edit.text().strip() and not self.serial_edit.text().strip():
            QMessageBox.warning(
                self, "Validation",
                "Please provide at least a model or a serial number.",
            )
            return
        self.accept()

    # --------------------------------------------------------------- output
    def to_item(self) -> Item:
        warranty = ""
        if self.warranty_check.isChecked():
            d = self.warranty_edit.date()
            warranty = d.toString("yyyy-MM-dd") if d.isValid() else ""

        base = self._item or Item()
        base.group_name = self.group_edit.currentText().strip()
        base.type = self.type_edit.currentText().strip()
        base.brand = self.brand_edit.currentText().strip()
        base.model = self.model_edit.text().strip()
        base.serial = self.serial_edit.text().strip()
        base.store = self.store_edit.currentText().strip()
        base.location = self.location_edit.currentText().strip()
        base.status = self.status_combo.currentText()
        base.quantity = self.qty_spin.value()
        base.purchase_date = self.purchase_edit.date().toString("yyyy-MM-dd")
        base.warranty_end = warranty
        base.info = self.info_edit.toPlainText().strip()
        base.image_path = self._image_path
        return base
