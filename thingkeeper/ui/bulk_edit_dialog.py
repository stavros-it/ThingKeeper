"""Bulk edit dialog — apply one field change to many items at once."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from .. import config

# Fields that can be bulk-edited: (column, label, widget-type).
_EDITABLE_FIELDS = [
    ("group_name", "Group", "combo"),
    ("type", "Type", "combo"),
    ("brand", "Brand", "combo"),
    ("status", "Status", "combo"),
    ("location", "Location", "combo"),
    ("store", "Store", "combo"),
]


class BulkEditDialog(QDialog):
    """Choose a field and a new value; applies to all selected items."""

    def __init__(self, parent: QWidget | None = None, count: int = 0) -> None:
        super().__init__(parent)
        self._count = count
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("ThingKeeper — Bulk edit")
        self.setMinimumWidth(420)

        info = QLabel(
            f"Apply a single field change to {self._count} selected item(s)."
        )
        info.setWordWrap(True)

        self.field_combo = QComboBox()
        for col, label, _kind in _EDITABLE_FIELDS:
            self.field_combo.addItem(label, col)
        self.field_combo.currentIndexChanged.connect(self._on_field_changed)

        self.value_widget = QWidget()
        self.value_layout = QHBoxLayout(self.value_widget)
        self.value_layout.setContentsMargins(0, 0, 0, 0)
        self._value_combo = QComboBox()
        self._value_combo.setEditable(True)
        self.value_layout.addWidget(self._value_combo)

        form = QFormLayout()
        form.addRow("Field:", self.field_combo)
        form.addRow("New value:", self.value_widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Apply).setText("Apply")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self._on_field_changed(0)

    def _on_field_changed(self, _idx: int) -> None:
        from ..repository import distinct_values

        col = self.field_combo.currentData()
        self._value_combo.clear()
        if col == "status":
            self._value_combo.addItems(config.STATUSES)
        else:
            self._value_combo.addItems(distinct_values(col))
        self._value_combo.setCurrentText("")
        self._value_combo.setFocus()

    def selected_field(self) -> str:
        return self.field_combo.currentData()

    def selected_value(self) -> str:
        return self._value_combo.currentText().strip()
