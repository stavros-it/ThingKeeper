"""Loan dialog — open a new loan for an item."""

from __future__ import annotations

from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..repository import Item, list_contacts


class LoanDialog(QDialog):
    """Open a loan for a specific item. Pre-fills item details."""

    def __init__(
        self,
        parent: QWidget | None = None,
        item: Item | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("ThingKeeper — Loan item")
        self.setMinimumWidth(440)
        self._item = item
        self._build_ui()
        if item is not None:
            self._load_item(item)

    def _build_ui(self) -> None:
        self.item_label = QLabel("")
        self.item_label.setStyleSheet("font-weight: bold;")

        self.contact_combo = QComboBox()
        self.contact_combo.addItem("(free text)", None)
        for c in list_contacts():
            self.contact_combo.addItem(f"{c.name} ({c.phone or c.email or ''})", c.id)
        self.contact_combo.currentIndexChanged.connect(self._on_contact_changed)

        self.borrower_edit = QLineEdit()
        self.borrower_edit.setPlaceholderText("Borrower name")

        self.loaned_edit = QDateEdit()
        self.loaned_edit.setCalendarPopup(True)
        self.loaned_edit.setDisplayFormat("yyyy-MM-dd")
        self.loaned_edit.setDate(date.today())
        self.loaned_edit.setEnabled(False)  # always today

        self.due_edit = QDateEdit()
        self.due_edit.setCalendarPopup(True)
        self.due_edit.setDisplayFormat("yyyy-MM-dd")
        self.due_edit.setDate(date.today() + timedelta(days=14))

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(70)

        form = QFormLayout()
        form.addRow("Item:", self.item_label)
        form.addRow("Contact:", self.contact_combo)
        form.addRow("Borrower:", self.borrower_edit)
        form.addRow("Loaned on:", self.loaned_edit)
        form.addRow("Due on:", self.due_edit)
        form.addRow("Notes:", self.notes_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Open loan")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _load_item(self, item: Item) -> None:
        label = f"#{item.id} — {(item.brand + ' ' + item.model).strip() or item.serial}"
        self.item_label.setText(label)

    def _on_contact_changed(self, _idx: int) -> None:
        cid = self.contact_combo.currentData()
        if cid is None:
            self.borrower_edit.clear()
            self.borrower_edit.setEnabled(True)
            return
        from ..repository import get_contact
        c = get_contact(cid)
        if c is not None:
            self.borrower_edit.setText(c.name)
            self.borrower_edit.setEnabled(False)

    def _validate_and_accept(self) -> None:
        if not self.borrower_edit.text().strip():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Validation", "Please provide a borrower name.")
            return
        self.accept()

    def contact_id(self) -> int | None:
        return self.contact_combo.currentData()

    def borrower(self) -> str:
        return self.borrower_edit.text().strip()

    def due_on(self) -> str:
        return self.due_edit.date().toString("yyyy-MM-dd")

    def notes(self) -> str:
        return self.notes_edit.toPlainText().strip()
