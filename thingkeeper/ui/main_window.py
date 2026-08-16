"""Main application window: table, filters, menus, toolbar, import/export."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .. import config
from ..exporters import export_archive, export_csv, export_excel
from ..importers import import_archive, import_csv, import_excel
from ..repository import (
    Item,
    delete_item,
    distinct_values,
    list_items,
    total_quantity,
    warranty_expired,
    warranty_expiring,
)
from .item_dialog import ItemDialog
from .reports_dialog import ReportsDialog
from .scan_dialog import ScanDialog

COLUMNS = [
    ("ID", 50),
    ("Group", 110),
    ("Type", 120),
    ("Brand", 110),
    ("Model", 240),
    ("Serial", 140),
    ("Status", 100),
    ("Qty", 50),
    ("Location", 120),
    ("Purchase", 100),
    ("Warranty", 100),
    ("Store", 100),
]

STATUS_COLORS = {
    "AVAILABLE": "#1a7a1a",
    "IN USE": "#1f5fa8",
    "LOANED": "#9a6a00",
    "BROKEN": "#a02020",
    "SOLD": "#666666",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{config.APP_NAME} {config.APP_VERSION}")
        self.resize(1280, 760)
        self._items: list[Item] = []
        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
        self.refresh()
        # Live search debounce.
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._search_timer.timeout.connect(self.refresh)

    # --------------------------------------------------------------- layout
    def _build_ui(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        # Filter bar.
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search group, type, brand, model, serial, location…")
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.search_edit.setClearButtonEnabled(True)

        self.group_combo = self._filter_combo("group_name")
        self.type_combo = self._filter_combo("type")
        self.brand_combo = self._filter_combo("brand")
        self.status_combo = QComboBox()
        self.status_combo.addItem("(all statuses)", "")
        for s in config.STATUSES:
            self.status_combo.addItem(s, s)
        for combo in (self.group_combo, self.type_combo, self.brand_combo, self.status_combo):
            combo.currentIndexChanged.connect(self.refresh)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_filters)

        filters = QHBoxLayout()
        filters.addWidget(self.search_edit, 1)
        filters.addWidget(QLabel("Group:"))
        filters.addWidget(self.group_combo)
        filters.addWidget(QLabel("Type:"))
        filters.addWidget(self.type_combo)
        filters.addWidget(QLabel("Brand:"))
        filters.addWidget(self.brand_combo)
        filters.addWidget(QLabel("Status:"))
        filters.addWidget(self.status_combo)
        filters.addWidget(clear_btn)
        outer.addLayout(filters)

        # Table.
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        header = self.table.horizontalHeader()
        for i, (_, w) in enumerate(COLUMNS):
            header.resizeSection(i, w)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self.edit_selected)
        self.table.itemSelectionChanged.connect(self._update_actions)
        outer.addWidget(self.table, 1)

        self.setCentralWidget(central)

    def _filter_combo(self, column: str) -> QComboBox:
        combo = QComboBox()
        combo.addItem(f"(all {column})", "")
        combo.addItems(distinct_values(column))
        combo.setMinimumWidth(140)
        return combo

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setIconSize(tb.iconSize())
        self.addToolBar(tb)

        self.act_new = QAction("New", self)
        self.act_new.setShortcut("Ctrl+N")
        self.act_new.triggered.connect(self.new_item)
        tb.addAction(self.act_new)

        self.act_edit = QAction("Edit", self)
        self.act_edit.setShortcut("Ctrl+E")
        self.act_edit.triggered.connect(self.edit_selected)
        tb.addAction(self.act_edit)

        self.act_delete = QAction("Delete", self)
        self.act_delete.setShortcut("Delete")
        self.act_delete.triggered.connect(self.delete_selected)
        tb.addAction(self.act_delete)

        tb.addSeparator()
        self.act_scan = QAction("Scan", self)
        self.act_scan.setShortcut("Ctrl+K")
        self.act_scan.triggered.connect(self.scan_serial)
        tb.addAction(self.act_scan)

        self.act_report = QAction("Report", self)
        self.act_report.triggered.connect(self.generate_report)
        tb.addAction(self.act_report)

        tb.addSeparator()
        self.act_refresh = QAction("Refresh", self)
        self.act_refresh.setShortcut("F5")
        self.act_refresh.triggered.connect(self.refresh)
        tb.addAction(self.act_refresh)

        self._update_actions()

    def _build_menu(self) -> None:
        mb = self.menuBar()

        file_menu = mb.addMenu("&File")

        imp_menu = file_menu.addMenu("&Import")
        self._add_action(imp_menu, "Excel workbook (.xlsx)…", self._import_excel)
        self._add_action(imp_menu, "ThingKeeper archive (.tkz)…", self._import_archive)
        self._add_action(imp_menu, "CSV (.csv)…", self._import_csv)

        exp_menu = file_menu.addMenu("&Export")
        self._add_action(exp_menu, "ThingKeeper archive (.tkz)…", self._export_archive)
        self._add_action(exp_menu, "Excel workbook (.xlsx)…", self._export_excel)
        self._add_action(exp_menu, "CSV (.csv)…", self._export_csv)

        file_menu.addSeparator()
        self._add_action(file_menu, "Generate &report (PDF)…", self.generate_report, "Ctrl+R")
        file_menu.addSeparator()
        self._add_action(file_menu, "&Quit", self.close, "Ctrl+Q")

        edit_menu = mb.addMenu("&Edit")
        self._add_action(edit_menu, "&New item", self.new_item, "Ctrl+N")
        self._add_action(edit_menu, "&Edit item", self.edit_selected, "Ctrl+E")
        self._add_action(edit_menu, "&Delete item", self.delete_selected, "Delete")

        view_menu = mb.addMenu("&View")
        self._add_action(view_menu, "&Refresh", self.refresh, "F5")
        self._add_action(view_menu, "&Scan serial", self.scan_serial, "Ctrl+K")
        self._add_action(view_menu, "&Clear filters", self._clear_filters)

        help_menu = mb.addMenu("&Help")
        self._add_action(help_menu, "&About", self._about)

    def _add_action(self, menu, text, slot, shortcut=None) -> None:
        act = QAction(text, self)
        if shortcut:
            act.setShortcut(shortcut)
        act.triggered.connect(slot)
        menu.addAction(act)

    def _build_statusbar(self) -> None:
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.count_label = QLabel("0 items")
        sb.addPermanentWidget(self.count_label)

    # ------------------------------------------------------------- data view
    def _on_search_changed(self) -> None:
        self._search_timer.start()

    def _clear_filters(self) -> None:
        self.search_edit.clear()
        for combo in (self.group_combo, self.type_combo, self.brand_combo):
            combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.refresh()

    def _current_filters(self) -> dict:
        return dict(
            search=self.search_edit.text().strip(),
            group=self.group_combo.currentData(),
            type_=self.type_combo.currentData(),
            brand=self.brand_combo.currentData(),
            status=self.status_combo.currentData(),
        )

    def refresh(self) -> None:
        f = self._current_filters()
        self._items = list_items(**f)
        self._populate_table(self._items)
        self.count_label.setText(
            f"{len(self._items)} items shown · {total_quantity()} total qty"
        )
        # Refresh filter dropdown options without losing current selection.
        self._refresh_filter_options()

    def _refresh_filter_options(self) -> None:
        for combo, column in (
            (self.group_combo, "group_name"),
            (self.type_combo, "type"),
            (self.brand_combo, "brand"),
        ):
            current = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(f"(all {column})", "")
            combo.addItems(distinct_values(column))
            if current:
                idx = combo.findData(current)
                combo.setCurrentIndex(idx if idx >= 0 else 0)
            combo.blockSignals(False)

    def _populate_table(self, items: list[Item]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(items))
        expired_serials = {it.id for it in warranty_expired()}
        soon_serials = {it.id for it in warranty_expiring()}

        for row, it in enumerate(items):
            cells = [
                str(it.id) if it.id is not None else "",
                it.group_name,
                it.type,
                it.brand,
                it.model,
                it.serial,
                it.status,
                str(it.quantity),
                it.location,
                it.purchase_date,
                it.warranty_end,
                it.store,
            ]
            for col, value in enumerate(cells):
                item = QTableWidgetItem(value)
                # Numeric sort for ID and Qty columns.
                if col in (0, 7):
                    item.setData(Qt.ItemDataRole.DisplayRole, value)
                    try:
                        item.setData(Qt.ItemDataRole.UserRole, int(value))
                    except (ValueError, TypeError):
                        pass
                # Status colouring.
                if col == 6:
                    color = STATUS_COLORS.get(it.status, "#333333")
                    item.setForeground(QColor(color))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                # Warranty colouring.
                if col == 10 and it.id in expired_serials:
                    item.setForeground(QColor("#a02020"))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                elif col == 10 and it.id in soon_serials:
                    item.setForeground(QColor("#9a6a00"))
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self._update_actions()

    # --------------------------------------------------------------- actions
    def _update_actions(self) -> None:
        has_selection = bool(self.table.selectionModel().selectedRows())
        self.act_edit.setEnabled(has_selection)
        self.act_delete.setEnabled(has_selection)

    def _selected_items(self) -> list[Item]:
        rows = {idx.row() for idx in self.table.selectionModel().selectedRows()}
        return [self._items[r] for r in sorted(rows)]

    def new_item(self) -> None:
        dlg = ItemDialog(self)
        if dlg.exec() == ItemDialog.DialogCode.Accepted:
            from ..repository import create_item
            item = dlg.to_item()
            create_item(item)
            self.refresh()

    def edit_selected(self) -> None:
        items = self._selected_items()
        if not items:
            return
        from ..repository import update_item
        for it in items:
            dlg = ItemDialog(self, item=it)
            if dlg.exec() == ItemDialog.DialogCode.Accepted:
                updated = dlg.to_item()
                updated.id = it.id
                update_item(updated)
            else:
                break
        self.refresh()

    def delete_selected(self) -> None:
        items = self._selected_items()
        if not items:
            return
        names = ", ".join(
            f"#{it.id} ({(it.brand + ' ' + it.model).strip() or it.serial})"
            for it in items[:8]
        )
        more = "" if len(items) <= 8 else f" … and {len(items) - 8} more"
        if QMessageBox.question(
            self, "Delete items",
            f"Delete {len(items)} item(s)?\n\n{names}{more}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        for it in items:
            delete_item(it.id)
        self.refresh()

    def scan_serial(self) -> None:
        dlg = ScanDialog(self)
        if dlg.exec() != ScanDialog.DialogCode.Accepted:
            return
        if dlg.matched_item is not None:
            # Open edit dialog for the matched item.
            edit = ItemDialog(self, item=dlg.matched_item)
            if edit.exec() == ItemDialog.DialogCode.Accepted:
                from ..repository import update_item
                updated = edit.to_item()
                updated.id = dlg.matched_item.id
                update_item(updated)
            self.refresh()
        elif dlg.pending_serial:
            # Pre-fill a new item with the scanned serial.
            new_dlg = ItemDialog(self)
            new_dlg.serial_edit.setText(dlg.pending_serial)
            if new_dlg.exec() == ItemDialog.DialogCode.Accepted:
                from ..repository import create_item
                create_item(new_dlg.to_item())
            self.refresh()

    def generate_report(self) -> None:
        ReportsDialog(self).exec()

    # ------------------------------------------------------------- importers
    def _import_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Excel", "", "Excel (*.xlsx *.xlsm)"
        )
        if not path:
            return
        self._run_import(lambda: import_excel(path), f"Imported from {Path(path).name}")

    def _import_archive(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import archive", "",
            f"ThingKeeper archive (*{config.ARCHIVE_EXT});;All files (*.*)",
        )
        if not path:
            return
        self._run_import(lambda: import_archive(path), f"Restored from {Path(path).name}")

    def _import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "", "CSV (*.csv)"
        )
        if not path:
            return
        self._run_import(lambda: import_csv(path), f"Imported from {Path(path).name}")

    def _run_import(self, fn, success_title: str) -> None:
        try:
            result = fn()
        except Exception as exc:  # pragma: no cover - defensive
            QMessageBox.critical(self, "Import failed", str(exc))
            return
        self.refresh()
        msg = (
            f"{success_title}\n\n"
            f"Imported: {result.imported}\n"
            f"Skipped:  {result.skipped}"
        )
        if result.errors:
            preview = "\n".join(result.errors[:10])
            more = "" if len(result.errors) <= 10 else f"\n…and {len(result.errors) - 10} more"
            msg += f"\n\nErrors ({len(result.errors)}):\n{preview}{more}"
        QMessageBox.information(self, "Import", msg)

    # ------------------------------------------------------------- exporters
    def _export_archive(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export archive", "thingkeeper_backup" + config.ARCHIVE_EXT,
            f"ThingKeeper archive (*{config.ARCHIVE_EXT})",
        )
        if not path:
            return
        self._run_export(export_archive, path, "archive")

    def _export_excel(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Excel", "thingkeeper.xlsx", "Excel (*.xlsx)"
        )
        if not path:
            return
        self._run_export(export_excel, path, "Excel")

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "thingkeeper.csv", "CSV (*.csv)"
        )
        if not path:
            return
        self._run_export(export_csv, path, "CSV")

    def _run_export(self, fn, path: str, label: str) -> None:
        try:
            fn(path)
        except Exception as exc:  # pragma: no cover - defensive
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        QMessageBox.information(self, "Export", f"{label} saved to:\n{path}")

    # ------------------------------------------------------------------ misc
    def _about(self) -> None:
        QMessageBox.about(
            self, f"About {config.APP_NAME}",
            f"<h3>{config.APP_NAME} {config.APP_VERSION}</h3>"
            "<p>Desktop inventory app for gadgets, appliances and hardware parts.</p>"
            "<p>PyQt6 + SQLite. Licensed under the MIT License.</p>"
        )

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.matches(QKeySequence.StandardKey.Find):
            self.search_edit.setFocus()
            self.search_edit.selectAll()
            return
        super().keyPressEvent(event)
