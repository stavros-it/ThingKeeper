"""Trash dialog — view, restore or permanently purge soft-deleted items."""

from __future__ import annotations

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..repository import hard_delete, list_trash, restore_item

_COLUMNS = [
    ("ID", 50),
    ("Deleted", 140),
    ("Group", 110),
    ("Type", 110),
    ("Brand", 110),
    ("Model", 200),
    ("Serial", 140),
]


class TrashDialog(QDialog):
    """View items in the trash; restore or purge them."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.setWindowTitle("ThingKeeper — Trash")
        self.resize(800, 500)
        self.setMinimumSize(600, 350)

        info = QLabel(
            "Deleted items are kept here. They are automatically purged after 30 days."
        )
        info.setStyleSheet("color: #666;")

        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in _COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        for i, (_, w) in enumerate(_COLUMNS):
            header.resizeSection(i, w)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        self.restore_btn = QPushButton("Restore selected")
        self.restore_btn.clicked.connect(self._restore)
        self.purge_btn = QPushButton("Purge selected")
        self.purge_btn.clicked.connect(self._purge)
        self.purge_all_btn = QPushButton("Purge all")
        self.purge_all_btn.clicked.connect(self._purge_all)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        actions = QHBoxLayout()
        actions.addWidget(self.restore_btn)
        actions.addWidget(self.purge_btn)
        actions.addWidget(self.purge_all_btn)
        actions.addStretch(1)
        actions.addWidget(self.close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(self.table, 1)
        layout.addLayout(actions)

    def refresh(self) -> None:
        items = list_trash()
        self.table.setRowCount(len(items))
        for row, it in enumerate(items):
            cells = [
                str(it.id) if it.id is not None else "",
                it.deleted_at,
                it.group_name,
                it.type,
                it.brand,
                it.model,
                it.serial,
            ]
            for col, value in enumerate(cells):
                item = QTableWidgetItem(value)
                if col == 1:
                    item.setForeground(QColor("#a02020"))
                self.table.setItem(row, col, item)

    def _selected_ids(self) -> list[int]:
        return [
            int(self.table.item(idx.row(), 0).text())
            for idx in self.table.selectionModel().selectedRows()
            if self.table.item(idx.row(), 0)
        ]

    def _restore(self) -> None:
        ids = self._selected_ids()
        for iid in ids:
            restore_item(iid)
        self.refresh()

    def _purge(self) -> None:
        ids = self._selected_ids()
        if not ids:
            return
        if QMessageBox.question(
            self, "Purge",
            f"Permanently delete {len(ids)} item(s)? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        for iid in ids:
            hard_delete(iid)
        self.refresh()

    def _purge_all(self) -> None:
        ids = [
            int(self.table.item(r, 0).text())
            for r in range(self.table.rowCount())
            if self.table.item(r, 0)
        ]
        if not ids:
            return
        if QMessageBox.question(
            self, "Purge all",
            f"Permanently delete all {len(ids)} items in trash? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        for iid in ids:
            hard_delete(iid)
        self.refresh()
