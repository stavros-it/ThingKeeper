"""Serial / barcode scan dialog.

Designed for USB keyboard-wedge scanners: focus is grabbed on open and
returned to the input after each lookup so the operator can keep scanning.
"""

from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..repository import Item
from ..scanner import lookup_serial


class ScanDialog(QDialog):
    """Scan serials and either open the matching item or create a new one."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.matched_item: Item | None = None
        self.pending_serial: str = ""
        self._build_ui()
        QTimer.singleShot(0, self.serial_edit.setFocus)

    def _build_ui(self) -> None:
        self.setWindowTitle("ThingKeeper — Scan serial")
        self.setMinimumWidth(480)

        title = QLabel("Scan or type a serial number")
        title.setStyleSheet("font-weight:bold; font-size:13px;")
        hint = QLabel(
            "Tip: a USB barcode scanner types the code and presses Enter — "
            "just leave this window focused."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#666;")

        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("Serial number…")
        self.serial_edit.returnPressed.connect(self._on_lookup)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(28)

        self.open_btn = QPushButton("Open item")
        self.open_btn.clicked.connect(self._open_matched)
        self.open_btn.setEnabled(False)
        self.new_btn = QPushButton("New item with this serial")
        self.new_btn.clicked.connect(self._create_new)
        self.new_btn.setEnabled(False)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addWidget(self.open_btn)
        actions.addWidget(self.new_btn)
        actions.addStretch(1)
        actions.addWidget(self.close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addSpacing(8)
        form = QFormLayout()
        form.addRow("Serial:", self.serial_edit)
        layout.addLayout(form)
        layout.addWidget(self.status_label)
        layout.addLayout(actions)

    # ---------------------------------------------------------------- logic
    def _set_status(self, text: str, ok: bool) -> None:
        self.status_label.setText(text)
        color = "#1a7a1a" if ok else "#a02020"
        self.status_label.setStyleSheet(f"color:{color}; font-weight:bold;")

    def _on_lookup(self) -> None:
        serial = self.serial_edit.text().strip()
        if not serial:
            return
        item = lookup_serial(serial)
        self.pending_serial = serial
        if item is not None:
            self.matched_item = item
            label = f"{item.brand} {item.model}".strip()
            self._set_status(
                f"Match: {label or 'item'} (id {item.id}, status {item.status})",
                ok=True,
            )
            self.open_btn.setEnabled(True)
            self.new_btn.setEnabled(False)
        else:
            self.matched_item = None
            self._set_status("No match — create a new item?", ok=False)
            self.open_btn.setEnabled(False)
            self.new_btn.setEnabled(True)
        self.serial_edit.clear()
        self.serial_edit.setFocus()

    def _open_matched(self) -> None:
        if self.matched_item is not None:
            self.done(self.DialogCode.Accepted)

    def _create_new(self) -> None:
        # Signal to caller that a new item should be pre-filled with the serial.
        self.matched_item = None
        self.done(self.DialogCode.Accepted)
