"""Loan history dialog — view all loans for a single item."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..repository import list_item_loans

_COLUMNS = [
    ("Loan ID", 60),
    ("Borrower", 160),
    ("Loaned", 100),
    ("Due", 100),
    ("Returned", 100),
    ("Notes", 220),
]


class LoanHistoryDialog(QDialog):
    """Show the full loan history for a single item (read-only)."""

    def __init__(self, item_id: int, item_label: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ThingKeeper — Loan history")
        self.resize(760, 440)
        self.setMinimumSize(560, 320)
        self._build_ui(item_label)
        self._load(item_id)

    def _build_ui(self, item_label: str) -> None:
        title = QLabel(f"Loan history — {item_label}")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")

        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in _COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        for i, (_, w) in enumerate(_COLUMNS):
            header.resizeSection(i, w)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.table, 1)
        layout.addLayout(actions)

    def _load(self, item_id: int) -> None:
        loans = list_item_loans(item_id)
        self.table.setRowCount(len(loans))
        for row, loan in enumerate(loans):
            cells = [
                str(loan.id) if loan.id is not None else "",
                loan.borrower,
                loan.loaned_on,
                loan.due_on,
                loan.returned_on or "— open —",
                loan.notes,
            ]
            for col, value in enumerate(cells):
                self.table.setItem(row, col, QTableWidgetItem(value))
