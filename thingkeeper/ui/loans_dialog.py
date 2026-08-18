"""Loans overview dialog — view open/all loans and return items."""

from __future__ import annotations

from datetime import date

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..repository import (
    get_item,
    list_loans,
    return_loan,
)
from .theme import DANGER

_COLUMNS = [
    ("Loan ID", 60),
    ("Item", 220),
    ("Serial", 130),
    ("Borrower", 140),
    ("Loaned", 100),
    ("Due", 100),
    ("Returned", 100),
    ("Notes", 180),
]


class LoansDialog(QDialog):
    """Browse loans (open / all) and return items."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ThingKeeper — Loans")
        self.resize(1000, 560)
        self.setMinimumSize(700, 400)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.open_only_check = QCheckBox("Open loans only")
        self.open_only_check.setChecked(True)
        self.open_only_check.toggled.connect(self.refresh)
        self.overdue_only_check = QCheckBox("Overdue only")
        self.overdue_only_check.toggled.connect(self.refresh)

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
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.return_btn = QPushButton("Return selected")
        self.return_btn.clicked.connect(self._return_selected)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        filters = QHBoxLayout()
        filters.addWidget(self.open_only_check)
        filters.addWidget(self.overdue_only_check)
        filters.addStretch(1)

        actions = QHBoxLayout()
        actions.addWidget(self.return_btn)
        actions.addStretch(1)
        actions.addWidget(self.refresh_btn)
        actions.addWidget(self.close_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(filters)
        layout.addWidget(self.table, 1)
        layout.addLayout(actions)

    def refresh(self) -> None:
        loans = list_loans(
            open_only=self.open_only_check.isChecked(),
            overdue_only=self.overdue_only_check.isChecked(),
        )
        self.table.setRowCount(len(loans))
        today_str = date.today().isoformat()
        for row, loan in enumerate(loans):
            item = get_item(loan.item_id) if loan.item_id is not None else None
            item_label = ""
            if item is not None:
                item_label = f"#{item.id} {(item.brand + ' ' + item.model).strip() or item.serial}"
            cells = [
                str(loan.id) if loan.id is not None else "",
                item_label,
                item.serial if item is not None else "",
                loan.borrower,
                loan.loaned_on,
                loan.due_on,
                loan.returned_on,
                loan.notes,
            ]
            for col, value in enumerate(cells):
                cell = QTableWidgetItem(value)
                if col == 5 and loan.is_open and loan.due_on and loan.due_on < today_str:
                    cell.setForeground(QColor(DANGER))
                    f = cell.font()
                    f.setBold(True)
                    cell.setFont(f)
                self.table.setItem(row, col, cell)
        self._update_actions()

    def _update_actions(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        enabled = False
        if rows:
            loan_id = self._selected_loan_id()
            if loan_id is not None:
                from ..repository import get_loan
                loan = get_loan(loan_id)
                enabled = loan.is_open if loan else False
        self.return_btn.setEnabled(enabled)

    def _selected_loan_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        return int(item.text()) if item else None

    def _return_selected(self) -> None:
        loan_id = self._selected_loan_id()
        if loan_id is None:
            return
        if QMessageBox.question(
            self, "Return item",
            f"Mark loan #{loan_id} as returned?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        return_loan(loan_id)
        self.refresh()
