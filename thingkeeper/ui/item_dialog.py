"""Add/Edit item dialog with multi-image gallery, warranty and drag-and-drop."""

from __future__ import annotations

import shutil
import uuid
from datetime import date
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import config
from ..repository import Item, distinct_values, list_images, list_receipts
from .date_fmt import qt_date_format
from .sizing import size_to_available

_IMAGE_FILTERS = "Images (*.png *.jpg *.jpeg *.bmp *.webp *.gif);;All files (*.*)"
_RECEIPT_FILTERS = (
    "Receipts (*.png *.jpg *.jpeg *.bmp *.webp *.gif *.pdf);;All files (*.*)"
)


class ItemDialog(QDialog):
    """Modal dialog for creating or editing an Item."""

    def __init__(self, parent: QWidget | None = None, item: Item | None = None) -> None:
        super().__init__(parent)
        self._item = item
        self._image_path: str = ""
        self._extra_images: list[str] = []
        self._receipts: list[str] = []
        self._build_ui()
        if item is not None:
            self._load_item(item)
        self.setAcceptDrops(True)

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.setWindowTitle("ThingKeeper — Item")
        self.setMinimumWidth(680)

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

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0.0, 1_000_000_000.0)
        self.price_spin.setDecimals(2)
        self.price_spin.setSingleStep(10.0)
        self.price_spin.setValue(0.0)

        self.depreciation_spin = QDoubleSpinBox()
        self.depreciation_spin.setRange(0.0, 100.0)
        self.depreciation_spin.setDecimals(1)
        self.depreciation_spin.setSingleStep(1.0)
        self.depreciation_spin.setValue(0.0)
        self.depreciation_spin.setSuffix(" yrs")

        self.purchase_edit = QDateEdit()
        self.purchase_edit.setCalendarPopup(True)
        self.purchase_edit.setDisplayFormat(qt_date_format())
        self.purchase_edit.setDate(date.today())
        self.purchase_edit.dateChanged.connect(self._on_purchase_changed)

        self.warranty_edit = QDateEdit()
        self.warranty_edit.setCalendarPopup(True)
        self.warranty_edit.setDisplayFormat(qt_date_format())
        self.warranty_edit.setDate(date.today())
        self.warranty_check = QCheckBox("Has warranty")
        self.warranty_check.toggled.connect(self._on_warranty_toggled)
        self._on_warranty_toggled(False)

        self.info_edit = QTextEdit()
        self.info_edit.setMaximumHeight(80)

        # Primary image preview + extras list, grouped in one section.
        # Primary image.
        self.image_label = QLabel("No image")
        self.image_label.setFixedSize(200, 150)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            "QLabel { background:#181818; border:1px dashed #3a3a3a; "
            "border-radius:6px; color:#9a9a9a; }"
        )
        self.image_label.setAcceptDrops(True)
        self.attach_btn = QPushButton("Choose…")
        self.attach_btn.clicked.connect(self._choose_primary_image)
        self.clear_img_btn = QPushButton("Remove")
        self.clear_img_btn.clicked.connect(self._clear_primary_image)

        img_row = QHBoxLayout()
        img_row.addWidget(self.image_label)
        img_col = QVBoxLayout()
        img_col.addWidget(self.attach_btn)
        img_col.addWidget(self.clear_img_btn)
        img_col.addStretch(1)
        img_row.addLayout(img_col, 1)
        img_widget = QWidget()
        img_widget.setLayout(img_row)

        # Extra images list (open via OS handler, no in-list preview).
        self.extra_list = QListWidget()
        self.extra_list.setIconSize(QSize(60, 60))
        self.extra_list.setMaximumHeight(110)
        self.extra_list.setAcceptDrops(True)
        self.extra_add_btn = QPushButton("Add…")
        self.extra_add_btn.clicked.connect(self._add_extra_image)
        self.extra_open_btn = QPushButton("Open")
        self.extra_open_btn.clicked.connect(self._open_extra_image)
        self.extra_remove_btn = QPushButton("Remove")
        self.extra_remove_btn.clicked.connect(self._remove_extra_image)

        extra_btns = QHBoxLayout()
        extra_btns.addWidget(self.extra_add_btn)
        extra_btns.addWidget(self.extra_open_btn)
        extra_btns.addWidget(self.extra_remove_btn)
        extra_btns.addStretch(1)
        extra_col = QVBoxLayout()
        extra_col.addWidget(self.extra_list)
        extra_col.addLayout(extra_btns)
        extra_widget = QWidget()
        extra_widget.setLayout(extra_col)

        # Combine primary preview + extras list into a single "Images" widget.
        images_col = QVBoxLayout()
        images_col.addWidget(img_widget)
        images_col.addWidget(extra_widget)
        images_widget = QWidget()
        images_widget.setLayout(images_col)

        # Receipts / invoices (image or PDF, no preview — open via OS handler).
        self.receipt_list = QListWidget()
        self.receipt_list.setIconSize(QSize(20, 20))
        self.receipt_list.setMaximumHeight(110)
        self.receipt_add_btn = QPushButton("Attach…")
        self.receipt_add_btn.clicked.connect(self._add_receipt)
        self.receipt_open_btn = QPushButton("Open")
        self.receipt_open_btn.clicked.connect(self._open_receipt)
        self.receipt_remove_btn = QPushButton("Remove")
        self.receipt_remove_btn.clicked.connect(self._remove_receipt)

        receipt_btns = QHBoxLayout()
        receipt_btns.addWidget(self.receipt_add_btn)
        receipt_btns.addWidget(self.receipt_open_btn)
        receipt_btns.addWidget(self.receipt_remove_btn)
        receipt_btns.addStretch(1)
        receipt_col = QVBoxLayout()
        receipt_col.addWidget(self.receipt_list)
        receipt_col.addLayout(receipt_btns)
        receipt_widget = QWidget()
        receipt_widget.setLayout(receipt_col)

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
        form.addRow("Unit price:", self.price_spin)
        form.addRow("Depreciation:", self.depreciation_spin)
        form.addRow("Store:", self.store_edit)
        form.addRow("Location:", self.location_edit)
        form.addRow("Purchase date:", self.purchase_edit)
        form.addRow("Warranty end:", warranty_widget)
        form.addRow("Notes:", self.info_edit)
        form.addRow("Images:", images_widget)
        form.addRow("Receipt / Invoice:", receipt_widget)

        form_widget = QWidget()
        form_widget.setLayout(form)
        scroll = QScrollArea()
        scroll.setWidget(form_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll, 1)
        layout.addWidget(buttons)

        size_to_available(self, 0.5, 0.95)

    def _combo_edit(self, column: str) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(distinct_values(column))
        return combo

    def _on_warranty_toggled(self, checked: bool) -> None:
        self.warranty_edit.setEnabled(checked)

    def _on_purchase_changed(self, new_date) -> None:
        """Auto-set warranty to 2 years after purchase if warranty is off
        or still equals the previous auto-calculated value."""
        from PyQt6.QtCore import QDate

        two_years = QDate(new_date.addYears(2))
        if not self.warranty_check.isChecked():
            self.warranty_check.setChecked(True)
            self.warranty_edit.setDate(two_years)
        elif self.warranty_edit.date() == new_date:
            self.warranty_edit.setDate(two_years)

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
        self.price_spin.setValue(item.unit_price)
        self.depreciation_spin.setValue(item.depreciation_years)
        self.purchase_edit.setDate(self._parse_date(item.purchase_date, date.today()))
        if item.warranty_end:
            self.warranty_check.setChecked(True)
            self.warranty_edit.setDate(self._parse_date(item.warranty_end, date.today()))
        self.info_edit.setPlainText(item.info)
        self._image_path = item.image_path
        self._refresh_primary_preview()
        if item.id is not None:
            for _img_id, path in list_images(item.id):
                self._extra_images.append(path)
            for _r_id, path in list_receipts(item.id):
                self._receipts.append(path)
            self._refresh_extra_list()
            self._refresh_receipt_list()

    @staticmethod
    def _parse_date(value: str, fallback: date) -> date:
        if not value:
            return fallback
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return fallback

    # --------------------------------------------------------- image helpers
    def _copy_to_attachments(self, source: str) -> str:
        ext = Path(source).suffix or ".img"
        target = config.ATTACHMENTS_DIR / f"{uuid.uuid4().hex}{ext}"
        shutil.copyfile(source, target)
        return str(target)

    def _choose_primary_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose image", "", _IMAGE_FILTERS)
        if not path:
            return
        try:
            self._image_path = self._copy_to_attachments(path)
        except OSError as exc:
            QMessageBox.warning(self, "Image", f"Could not copy image:\n{exc}")
            return
        self._refresh_primary_preview()

    def _clear_primary_image(self) -> None:
        self._image_path = ""
        self._refresh_primary_preview()

    def _refresh_primary_preview(self) -> None:
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

    def _add_extra_image(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose images", "", _IMAGE_FILTERS)
        for p in paths:
            try:
                self._extra_images.append(self._copy_to_attachments(p))
            except OSError as exc:
                QMessageBox.warning(self, "Image", f"Could not copy {p}:\n{exc}")
        self._refresh_extra_list()

    def _remove_extra_image(self) -> None:
        row = self.extra_list.currentRow()
        if 0 <= row < len(self._extra_images):
            self._extra_images.pop(row)
            self._refresh_extra_list()

    def _refresh_extra_list(self) -> None:
        self.extra_list.clear()
        for path in self._extra_images:
            name = Path(path).name
            item = QListWidgetItem(name)
            pix = QPixmap(path)
            if not pix.isNull():
                item.setIcon(
                    pix.scaled(
                        60, 60,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            self.extra_list.addItem(item)

    # ------------------------------------------------------- receipts / PDFs
    def _add_receipt(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Attach receipt", "", _RECEIPT_FILTERS)
        for p in paths:
            try:
                self._receipts.append(self._copy_to_attachments(p))
            except OSError as exc:
                QMessageBox.warning(self, "Receipt", f"Could not attach {p}:\n{exc}")
        self._refresh_receipt_list()

    def _remove_receipt(self) -> None:
        row = self.receipt_list.currentRow()
        if 0 <= row < len(self._receipts):
            self._receipts.pop(row)
            self._refresh_receipt_list()

    def _open_receipt(self) -> None:
        row = self.receipt_list.currentRow()
        if not (0 <= row < len(self._receipts)):
            return
        self._open_external(self._receipts[row], "Receipt")

    def _open_extra_image(self) -> None:
        row = self.extra_list.currentRow()
        if not (0 <= row < len(self._extra_images)):
            return
        self._open_external(self._extra_images[row], "Image")

    @staticmethod
    def _open_external(path: str, label: str) -> None:
        """Open a file via the OS default handler (no in-app preview)."""
        if not Path(path).exists():
            QMessageBox.information(None, label, "File no longer exists.")
            return
        import subprocess
        import sys
        if sys.platform == "win32":
            import os
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _refresh_receipt_list(self) -> None:
        self.receipt_list.clear()
        for path in self._receipts:
            self.receipt_list.addItem(QListWidgetItem(Path(path).name))

    # -------------------------------------------------------- drag-and-drop
    def dragEnterEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt override
        urls: list[QUrl] = event.mimeData().urls()
        added = False
        for url in urls:
            path = url.toLocalFile()
            if not path or not Path(path).is_file():
                continue
            try:
                self._extra_images.append(self._copy_to_attachments(path))
                added = True
            except OSError:
                continue
        if added:
            self._refresh_extra_list()
            event.acceptProposedAction()
        else:
            event.ignore()

    # --------------------------------------------------------- validation
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
        base.unit_price = self.price_spin.value()
        base.depreciation_years = self.depreciation_spin.value()
        base.purchase_date = self.purchase_edit.date().toString("yyyy-MM-dd")
        base.warranty_end = warranty
        base.info = self.info_edit.toPlainText().strip()
        base.image_path = self._image_path
        return base

    def extra_images(self) -> list[str]:
        """Return the list of extra image paths (excluding the primary image)."""
        return list(self._extra_images)

    def receipts(self) -> list[str]:
        """Return the list of receipt / invoice paths attached to the item."""
        return list(self._receipts)
