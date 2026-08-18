"""Contacts dialog — list, add, edit, delete contacts for loan tracking."""

from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..repository import (
    Contact,
    create_contact,
    delete_contact,
    list_contacts,
    update_contact,
)

_COLUMNS = [
    ("ID", 50),
    ("Name", 180),
    ("Phone", 140),
    ("Email", 200),
    ("Notes", 220),
]


class ContactEditDialog(QDialog):
    """Add or edit a single contact."""

    def __init__(self, parent: QWidget | None = None, contact: Contact | None = None) -> None:
        super().__init__(parent)
        self._contact = contact
        self.setWindowTitle("ThingKeeper — Contact")
        self.setMinimumWidth(420)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Full name")
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)

        form = QFormLayout()
        form.addRow("Name:", self.name_edit)
        form.addRow("Phone:", self.phone_edit)
        form.addRow("Email:", self.email_edit)
        form.addRow("Notes:", self.notes_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if contact is not None:
            self.name_edit.setText(contact.name)
            self.phone_edit.setText(contact.phone)
            self.email_edit.setText(contact.email)
            self.notes_edit.setPlainText(contact.notes)

    def _validate_and_accept(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Please provide a name.")
            return
        self.accept()

    def to_contact(self) -> Contact:
        base = self._contact or Contact()
        base.name = self.name_edit.text().strip()
        base.phone = self.phone_edit.text().strip()
        base.email = self.email_edit.text().strip()
        base.notes = self.notes_edit.toPlainText().strip()
        return base


class ContactsDialog(QDialog):
    """Browse, search, add, edit and delete contacts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ThingKeeper — Contacts")
        self.resize(800, 500)
        self.setMinimumSize(600, 350)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search name, phone, email…")
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.search_edit.setClearButtonEnabled(True)

        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in _COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._update_actions)
        header = self.table.horizontalHeader()
        for i, (_, w) in enumerate(_COLUMNS):
            header.resizeSection(i, w)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self._edit_selected)

        self.add_btn = QPushButton("Add…")
        self.add_btn.clicked.connect(self._add)
        self.edit_btn = QPushButton("Edit…")
        self.edit_btn.clicked.connect(self._edit_selected)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_selected)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        search_row.addWidget(self.search_edit, 1)
        actions = QHBoxLayout()
        actions.addWidget(self.add_btn)
        actions.addWidget(self.edit_btn)
        actions.addWidget(self.delete_btn)
        actions.addStretch(1)
        actions.addWidget(self.close_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(search_row)
        layout.addWidget(self.table, 1)
        layout.addLayout(actions)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self.refresh)

    def _on_search_changed(self) -> None:
        self._timer.start()

    def refresh(self) -> None:
        search = self.search_edit.text().strip()
        contacts = list_contacts(search)
        self.table.setRowCount(len(contacts))
        for row, c in enumerate(contacts):
            cells = [
                str(c.id) if c.id is not None else "",
                c.name,
                c.phone,
                c.email,
                c.notes,
            ]
            for col, value in enumerate(cells):
                self.table.setItem(row, col, QTableWidgetItem(value))
        self._update_actions()

    def _update_actions(self) -> None:
        has_sel = bool(self.table.selectionModel().selectedRows())
        self.edit_btn.setEnabled(has_sel)
        self.delete_btn.setEnabled(has_sel)

    def _selected_contact_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        return int(item.text()) if item else None

    def _add(self) -> None:
        dlg = ContactEditDialog(self)
        if dlg.exec() == ContactEditDialog.DialogCode.Accepted:
            create_contact(dlg.to_contact())
            self.refresh()

    def _edit_selected(self) -> None:
        cid = self._selected_contact_id()
        if cid is None:
            return
        from ..repository import get_contact
        contact = get_contact(cid)
        if contact is None:
            return
        dlg = ContactEditDialog(self, contact=contact)
        if dlg.exec() == ContactEditDialog.DialogCode.Accepted:
            updated = dlg.to_contact()
            update_contact(updated)
            self.refresh()

    def _delete_selected(self) -> None:
        cid = self._selected_contact_id()
        if cid is None:
            return
        if QMessageBox.question(
            self, "Delete contact",
            f"Delete contact #{cid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        delete_contact(cid)
        self.refresh()
