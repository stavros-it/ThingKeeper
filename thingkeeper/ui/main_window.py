"""Main application window: table, filters, menus, toolbar, import/export.

v0.2 features: undo/redo, bulk edit, duplicate, keyboard navigation,
column show/hide & ordering, saved filters, recent files, trash dialog,
multi-image support.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PyQt6.QtCore import QSettings, Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .. import backup as backup_mod
from .. import config
from ..commands import (
    BulkUpdateCommand,
    CreateItemCommand,
    DeleteItemCommand,
    DuplicateItemCommand,
    UndoStack,
    UpdateItemCommand,
)
from ..exporters import (
    export_archive,
    export_archive_encrypted,
    export_csv,
    export_excel,
    export_html,
    is_encrypted_archive,
)
from ..importers import (
    import_archive,
    import_archive_encrypted,
    import_csv,
    import_excel,
)
from ..repository import (
    Item,
    distinct_values,
    get_item,
    list_items,
    overdue_loan_item_ids,
    set_images,
    total_quantity,
)
from .bulk_edit_dialog import BulkEditDialog
from .integrity_dialog import IntegrityDialog
from .item_dialog import ItemDialog
from .reports_dialog import ReportsDialog
from .scan_dialog import ScanDialog
from .settings_dialog import SettingsDialog
from .theme import (
    DANGER,
    DANGER_BG,
    INFO,
    STATUS_COLORS,
    SUCCESS,
    TEXT,
    TEXT_DIM,
    WARNING,
    WARNING_BG,
)
from .trash_dialog import TrashDialog

COLUMNS = [
    ("ID", 50),
    ("Group", 110),
    ("Type", 120),
    ("Brand", 110),
    ("Model", 240),
    ("Status", 100),
    ("Comments", 200),
    ("Serial", 140),
    ("Qty", 50),
    ("Location", 120),
    ("Purchase", 100),
    ("Warranty", 100),
    ("Store", 100),
]

_SETTINGS_FILTERS = "filters/saved"
_SETTINGS_RECENT_IMP = "recent/imports"
_SETTINGS_RECENT_EXP = "recent/exports"
_SETTINGS_COL_VIS = "columns/visible"
_SETTINGS_COL_WIDTHS = "columns/widths"
_SETTINGS_SORT = "table/sort"


def _fmt_date(iso: str) -> str:
    """Convert an ISO date (YYYY-MM-DD) to DD-MM-YYYY for display."""
    if not iso or len(iso) < 10:
        return iso
    try:
        y, m, d = iso[:10].split("-")
        return f"{d}-{m}-{y}"
    except ValueError:
        return iso


def _days_until(iso: str) -> int | None:
    """Days from today until the given ISO date (negative = past)."""
    if not iso or len(iso) < 10:
        return None
    try:
        y, m, d = iso[:10].split("-")
        target = date(int(y), int(m), int(d))
    except ValueError:
        return None
    return (target - date.today()).days


def _warranty_status(it: Item) -> tuple[str, str, str, bool, bool, bool]:
    """Return (display_text, tooltip, fg_color, bg_color, bold, italic)
    for the warranty cell based on the item's warranty end date."""
    we = (it.warranty_end or "").strip()
    if not we:
        return ("", "No warranty", TEXT_DIM, "", False, True)
    days = _days_until(we)
    if days is None:
        return (_fmt_date(we), "", TEXT, "", False, False)
    disp = _fmt_date(we)
    if days < 0:
        abs_d = -days
        unit = "year" if abs_d >= 365 else "month" if abs_d >= 30 else "day"
        n = abs_d // 365 if unit == "year" else abs_d // 30 if unit == "month" else abs_d
        tip = f"Expired {n} {unit}{'s' if n != 1 else ''} ago"
        return (disp, tip, DANGER, DANGER_BG, True, False)
    if days == 0:
        return (disp, "Expires today", WARNING, WARNING_BG, True, False)
    if days <= config.WARRANTY_SOON_DAYS:
        tip = f"{days} day{'s' if days != 1 else ''} left"
        return (disp, tip, WARNING, WARNING_BG, False, False)
    years = days // 365
    months = (days % 365) // 30
    if years >= 1:
        tip = f"{years}y {months}m left" if months else f"{years}y left"
    elif months >= 1:
        tip = f"{months}m left"
    else:
        tip = f"{days} days left"
    return (disp, tip, SUCCESS, "", False, False)

_SETTINGS_COL_ORDER = "columns/order"
_MAX_RECENT = 8


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{config.APP_NAME} {config.APP_VERSION}")
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "app.ico"
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1280, 760)
        self._items: list[Item] = []
        self._settings = QSettings("ThingKeeper", "ThingKeeper")
        self._first_populate = True
        self.undo_stack = UndoStack()
        self.undo_stack.set_changed_callback(self._update_undo_actions)
        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
        self._restore_column_state()
        self.refresh()
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._search_timer.timeout.connect(self.refresh)
        self._backup_scheduler = backup_mod.BackupScheduler(self)
        self._backup_scheduler.backup_created.connect(self._on_auto_backup)
        self._backup_scheduler.backup_failed.connect(self._on_auto_backup_failed)
        self._backup_scheduler.start()
        backup_mod.maybe_auto_backup()

    # --------------------------------------------------------------- layout
    def _build_ui(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        # Filter bar.
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Search group, type, brand, model, serial, location…"
        )
        self.search_edit.setStatusTip("Filter items by text (Ctrl+F to focus)")
        self.search_edit.setAccessibleName("Search box")
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

        # Saved filters.
        self.saved_combo = QComboBox()
        self.saved_combo.setMinimumWidth(120)
        self.saved_combo.currentIndexChanged.connect(self._recall_filter)
        self._refresh_saved_combo()
        save_filter_btn = QPushButton("Save…")
        save_filter_btn.clicked.connect(self._save_filter)

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
        filters.addSpacing(12)
        filters.addWidget(QLabel("Presets:"))
        filters.addWidget(self.saved_combo)
        filters.addWidget(save_filter_btn)
        outer.addLayout(filters)

        # Table.
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in COLUMNS])
        self.table.setAccessibleName("Items table")
        self.table.setAccessibleDescription(
            "Inventory items. Double-click a row to edit it."
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setMinimumSectionSize(60)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_column_menu)
        header.sectionMoved.connect(self._on_section_moved)
        header.sortIndicatorChanged.connect(self._on_sort_changed)
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
        self.addToolBar(tb)

        self.act_new = QAction("New", self)
        self.act_new.setShortcut("Ctrl+N")
        self.act_new.setStatusTip("Create a new item")
        self.act_new.triggered.connect(self.new_item)
        tb.addAction(self.act_new)

        self.act_edit = QAction("Edit", self)
        self.act_edit.setShortcut("Ctrl+E")
        self.act_edit.setStatusTip("Edit the selected item")
        self.act_edit.triggered.connect(self.edit_selected)
        tb.addAction(self.act_edit)

        self.act_duplicate = QAction("Duplicate", self)
        self.act_duplicate.setShortcut("Ctrl+D")
        self.act_duplicate.setStatusTip("Duplicate the selected item")
        self.act_duplicate.triggered.connect(self.duplicate_selected)
        tb.addAction(self.act_duplicate)

        self.act_delete = QAction("Delete", self)
        self.act_delete.setShortcut("Delete")
        self.act_delete.setStatusTip("Move the selected item to trash")
        self.act_delete.triggered.connect(self.delete_selected)
        tb.addAction(self.act_delete)

        tb.addSeparator()
        self.act_undo = QAction("Undo", self)
        self.act_undo.setShortcut("Ctrl+Z")
        self.act_undo.setStatusTip("Undo the last action")
        self.act_undo.triggered.connect(self.undo_stack.undo)
        tb.addAction(self.act_undo)

        self.act_redo = QAction("Redo", self)
        self.act_redo.setShortcut("Ctrl+Y")
        self.act_redo.setStatusTip("Redo the last undone action")
        self.act_redo.triggered.connect(self.undo_stack.redo)
        tb.addAction(self.act_redo)

        tb.addSeparator()
        self.act_bulk_edit = QAction("Bulk edit", self)
        self.act_bulk_edit.setShortcut("Ctrl+B")
        self.act_bulk_edit.setStatusTip("Edit multiple selected items at once")
        self.act_bulk_edit.triggered.connect(self.bulk_edit)
        tb.addAction(self.act_bulk_edit)

        self.act_scan = QAction("Scan", self)
        self.act_scan.setShortcut("Ctrl+K")
        self.act_scan.setStatusTip("Look up an item by scanning its barcode")
        self.act_scan.triggered.connect(self.scan_serial)
        tb.addAction(self.act_scan)

        self.act_trash = QAction("Trash", self)
        self.act_trash.setStatusTip("View, restore, or purge deleted items")
        self.act_trash.triggered.connect(self.show_trash)
        tb.addAction(self.act_trash)

        self.act_loan = QAction("Loan", self)
        self.act_loan.setShortcut("Ctrl+L")
        self.act_loan.setStatusTip("Loan the selected item to a contact")
        self.act_loan.triggered.connect(self.loan_selected)
        tb.addAction(self.act_loan)

        self.act_loans = QAction("Loans", self)
        self.act_loans.setStatusTip("Browse all loans and return items")
        self.act_loans.triggered.connect(self.show_loans)
        tb.addAction(self.act_loans)

        self.act_contacts = QAction("Contacts", self)
        self.act_contacts.setStatusTip("Manage contacts for loans")
        tb.addAction(self.act_contacts)

        self.act_report = QAction("Report", self)
        self.act_report.triggered.connect(self.generate_report)
        tb.addAction(self.act_report)

        self.act_dashboard = QAction("Dashboard", self)
        self.act_dashboard.triggered.connect(self.show_dashboard)
        tb.addAction(self.act_dashboard)

        tb.addSeparator()
        self.act_refresh = QAction("Refresh", self)
        self.act_refresh.setShortcut("F5")
        self.act_refresh.triggered.connect(self.refresh)
        tb.addAction(self.act_refresh)

        self._update_actions()
        self._update_undo_actions()

    def _build_menu(self) -> None:
        mb = self.menuBar()

        file_menu = mb.addMenu("&File")

        self._imp_menu = file_menu.addMenu("&Import")
        self._add_action(self._imp_menu, "Excel workbook (.xlsx)…", self._import_excel)
        self._add_action(self._imp_menu, "ThingKeeper archive (.tkz)…", self._import_archive)
        self._add_action(self._imp_menu, "Encrypted archive (.tkz)…",
                         self._import_archive_encrypted)
        self._add_action(self._imp_menu, "CSV (.csv)…", self._import_csv)
        self._imp_menu.aboutToShow.connect(self._refresh_recent_imports)

        self._exp_menu = file_menu.addMenu("&Export")
        self._add_action(self._exp_menu, "ThingKeeper archive (.tkz)…", self._export_archive)
        self._add_action(self._exp_menu, "Encrypted archive (.tkz)…",
                         self._export_archive_encrypted)
        self._add_action(self._exp_menu, "Excel workbook (.xlsx)…", self._export_excel)
        self._add_action(self._exp_menu, "CSV (.csv)…", self._export_csv)
        self._add_action(self._exp_menu, "HTML (.html)…", self._export_html)
        self._exp_menu.aboutToShow.connect(self._refresh_recent_exports)

        file_menu.addSeparator()
        self._add_action(file_menu, "&Dashboard…", self.show_dashboard)
        self._add_action(file_menu, "Generate &report (PDF)…", self.generate_report, "Ctrl+R")
        self._add_action(file_menu, "Custom report &builder…", self.show_report_builder)
        file_menu.addSeparator()
        self._add_action(file_menu, "&Quit", self.close, "Ctrl+Q")

        edit_menu = mb.addMenu("&Edit")
        self._add_action(edit_menu, "&New item", self.new_item, "Ctrl+N")
        self._add_action(edit_menu, "&Edit item", self.edit_selected, "Ctrl+E")
        self._add_action(edit_menu, "&Duplicate item", self.duplicate_selected, "Ctrl+D")
        self._add_action(edit_menu, "&Delete item", self.delete_selected, "Delete")
        edit_menu.addSeparator()
        self._add_action(edit_menu, "&Undo", self.undo_stack.undo, "Ctrl+Z")
        self._add_action(edit_menu, "&Redo", self.undo_stack.redo, "Ctrl+Y")
        edit_menu.addSeparator()
        self._add_action(edit_menu, "&Bulk edit…", self.bulk_edit, "Ctrl+B")

        view_menu = mb.addMenu("&View")
        self._add_action(view_menu, "&Refresh", self.refresh, "F5")
        self._add_action(view_menu, "&Scan serial", self.scan_serial, "Ctrl+K")
        self._add_action(view_menu, "&Clear filters", self._clear_filters)
        self._add_action(view_menu, "&Dashboard…", self.show_dashboard)
        self._add_action(view_menu, "&Trash…", self.show_trash)
        view_menu.addSeparator()
        self._add_action(view_menu, "&Columns…", self._show_column_menu_at_zero)
        loans_menu = mb.addMenu("&Loans")

        self._add_action(loans_menu, "&Loan selected item…", self.loan_selected, "Ctrl+L")
        self._add_action(loans_menu, "&All loans…", self.show_loans)
        loans_menu.addSeparator()
        self._add_action(loans_menu, "&Contacts…", self.show_contacts)
        self._add_action(loans_menu, "Loan &history for selected…", self.show_loan_history)

        tools_menu = mb.addMenu("&Tools")
        self._add_action(tools_menu, "&Back up now…", self.backup_now)
        self._add_action(tools_menu, "&Restore from backup…", self.restore_from_backup)
        self._add_action(tools_menu, "Data &integrity check…", self.show_integrity)
        tools_menu.addSeparator()
        self._add_action(tools_menu, "&Settings…", self.show_settings)

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
        self.saved_combo.setCurrentIndex(0)
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
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(items))
        overdue_loan_ids = overdue_loan_item_ids()

        for row, it in enumerate(items):
            w_disp, w_tip, w_fg, w_bg, w_bold, w_italic = _warranty_status(it)
            cells = [
                str(it.id) if it.id is not None else "",
                it.group_name,
                it.type,
                it.brand,
                it.model,
                it.status,
                it.info,
                it.serial,
                str(it.quantity),
                it.location,
                _fmt_date(it.purchase_date),
                w_disp,
                it.store,
            ]
            for col, value in enumerate(cells):
                item = QTableWidgetItem(value)
                if col in (0, 8):
                    item.setData(Qt.ItemDataRole.DisplayRole, value)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    try:
                        item.setData(Qt.ItemDataRole.UserRole, int(value))
                    except (ValueError, TypeError):
                        pass
                if col == 5:
                    color = STATUS_COLORS.get(it.status, TEXT)
                    item.setForeground(QColor(color))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                if col == 11:
                    item.setForeground(QColor(w_fg))
                    if w_bg:
                        item.setBackground(QColor(w_bg))
                    f = item.font()
                    f.setBold(w_bold)
                    f.setItalic(w_italic)
                    item.setFont(f)
                    if w_tip:
                        item.setToolTip(w_tip)
                    item.setData(Qt.ItemDataRole.UserRole, it.warranty_end or "")
                # Overdue loan: highlight the status cell with a red background.
                if col == 5 and it.id in overdue_loan_ids:
                    item.setBackground(QColor(DANGER_BG))
                # Status row coloring (skip warranty cell, which has its own smart coloring).
                if col != 11:
                    if it.status == "BROKEN":
                        item.setForeground(QColor(DANGER))
                    elif it.status == "IN USE":
                        item.setForeground(QColor(INFO))
                self.table.setItem(row, col, item)
        if self._first_populate:
            self.table.resizeColumnsToContents()
            self._first_populate = False
            self._save_column_state()
        self.table.setUpdatesEnabled(True)
        self.table.setSortingEnabled(True)
        self._update_actions()

    # --------------------------------------------------------------- actions
    def _update_actions(self) -> None:
        has_selection = bool(self.table.selectionModel().selectedRows())
        self.act_edit.setEnabled(has_selection)
        self.act_delete.setEnabled(has_selection)
        self.act_duplicate.setEnabled(has_selection)
        self.act_loan.setEnabled(has_selection)
        self.act_bulk_edit.setEnabled(has_selection)

    def _update_undo_actions(self) -> None:
        self.act_undo.setEnabled(self.undo_stack.can_undo)
        self.act_redo.setEnabled(self.undo_stack.can_redo)
        ul = self.undo_stack.undo_label()
        rl = self.undo_stack.redo_label()
        self.act_undo.setText(f"Undo {ul}" if ul else "Undo")
        self.act_redo.setText(f"Redo {rl}" if rl else "Redo")

    def _selected_items(self) -> list[Item]:
        rows = {idx.row() for idx in self.table.selectionModel().selectedRows()}
        result: list[Item] = []
        for r in sorted(rows):
            id_item = self.table.item(r, 0)
            if id_item is None:
                continue
            item_id = id_item.data(Qt.ItemDataRole.UserRole)
            if item_id is None:
                continue
            found = get_item(int(item_id))
            if found is not None:
                result.append(found)
        return result

    def new_item(self) -> None:
        dlg = ItemDialog(self)
        if dlg.exec() == ItemDialog.DialogCode.Accepted:
            item = dlg.to_item()
            cmd = CreateItemCommand(item)
            self.undo_stack.push(cmd)
            if item.id is not None:
                set_images(item.id, dlg.extra_images())
            self.refresh()

    def edit_selected(self) -> None:
        items = self._selected_items()
        if not items:
            return
        for it in items:
            old = get_item(it.id) or it
            dlg = ItemDialog(self, item=it)
            if dlg.exec() == ItemDialog.DialogCode.Accepted:
                updated = dlg.to_item()
                updated.id = it.id
                cmd = UpdateItemCommand(old, updated)
                self.undo_stack.push(cmd)
                set_images(it.id, dlg.extra_images())
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
            f"Move {len(items)} item(s) to trash?\n\n{names}{more}\n\n"
            "Items can be restored from the Trash for 30 days.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        cmd = DeleteItemCommand([it.id for it in items if it.id is not None])
        self.undo_stack.push(cmd)
        self.refresh()

    def duplicate_selected(self) -> None:
        items = self._selected_items()
        if not items:
            return
        for it in items:
            cmd = DuplicateItemCommand(it.id)
            self.undo_stack.push(cmd)
        self.refresh()

    def bulk_edit(self) -> None:
        items = self._selected_items()
        if not items:
            return
        dlg = BulkEditDialog(self, count=len(items))
        if dlg.exec() != BulkEditDialog.DialogCode.Accepted:
            return
        field = dlg.selected_field()
        value = dlg.selected_value()
        if not field:
            return
        ids = [it.id for it in items if it.id is not None]
        old_values = [
            {field: getattr(get_item(i), field, "") or ""} for i in ids
        ]
        cmd = BulkUpdateCommand(ids, old_values, {field: value})
        self.undo_stack.push(cmd)
        self.refresh()

    def scan_serial(self) -> None:
        dlg = ScanDialog(self)
        if dlg.exec() != ScanDialog.DialogCode.Accepted:
            return
        if dlg.matched_item is not None:
            old = get_item(dlg.matched_item.id) or dlg.matched_item
            edit = ItemDialog(self, item=dlg.matched_item)
            if edit.exec() == ItemDialog.DialogCode.Accepted:
                updated = edit.to_item()
                updated.id = dlg.matched_item.id
                cmd = UpdateItemCommand(old, updated)
                self.undo_stack.push(cmd)
                set_images(dlg.matched_item.id, edit.extra_images())
            self.refresh()
        elif dlg.pending_serial:
            new_dlg = ItemDialog(self)
            new_dlg.serial_edit.setText(dlg.pending_serial)
            if new_dlg.exec() == ItemDialog.DialogCode.Accepted:
                item = new_dlg.to_item()
                cmd = CreateItemCommand(item)
                self.undo_stack.push(cmd)
                if item.id is not None:
                    set_images(item.id, new_dlg.extra_images())
            self.refresh()

    def show_trash(self) -> None:
        dlg = TrashDialog(self)
        dlg.exec()
        self.refresh()

    def loan_selected(self) -> None:
        items = self._selected_items()
        if not items:
            QMessageBox.information(
                self, "Loan", "Select an item to loan out first."
            )
            return
        from ..repository import active_loan_for_item, open_loan
        from .loan_dialog import LoanDialog
        for it in items:
            active = active_loan_for_item(it.id) if it.id is not None else None
            if active is not None:
                QMessageBox.warning(
                    self, "Already on loan",
                    f"Item #{it.id} is already on loan to {active.borrower} "
                    f"(since {active.loaned_on}).",
                )
                continue
            dlg = LoanDialog(self, item=it)
            if dlg.exec() == LoanDialog.DialogCode.Accepted:
                open_loan(
                    it.id,
                    borrower=dlg.borrower(),
                    contact_id=dlg.contact_id(),
                    due_on=dlg.due_on(),
                    notes=dlg.notes(),
                )
            else:
                break
        self.refresh()

    def show_loans(self) -> None:
        from .loans_dialog import LoansDialog
        LoansDialog(self).exec()
        self.refresh()

    def show_contacts(self) -> None:
        from .contacts_dialog import ContactsDialog
        ContactsDialog(self).exec()

    def show_loan_history(self) -> None:
        items = self._selected_items()
        if not items:
            QMessageBox.information(self, "Loan history", "Select an item first.")
            return
        it = items[0]
        from .loan_history_dialog import LoanHistoryDialog
        label = f"#{it.id} {(it.brand + ' ' + it.model).strip() or it.serial}"
        LoanHistoryDialog(it.id, label, self).exec()

    def generate_report(self) -> None:
        ReportsDialog(self).exec()

    def show_dashboard(self) -> None:
        from .dashboard_dialog import DashboardDialog
        DashboardDialog(self).exec()

    def show_report_builder(self) -> None:
        from .report_builder_dialog import ReportBuilderDialog
        ReportBuilderDialog(self).exec()

    # --------------------------------------------------------- column state
    def _show_column_menu(self, pos) -> None:
        header = self.table.horizontalHeader()
        menu = QMenu(self)
        for i, (name, _) in enumerate(COLUMNS):
            act = QAction(name, self)
            act.setCheckable(True)
            act.setChecked(not self.table.isColumnHidden(i))
            act.toggled.connect(lambda checked, col=i: self._toggle_column(col, checked))
            menu.addAction(act)
        menu.addSeparator()
        reset = QAction("Reset to defaults", self)
        reset.triggered.connect(self._reset_columns)
        menu.addAction(reset)
        menu.exec(header.mapToGlobal(pos))

    def _show_column_menu_at_zero(self) -> None:
        self._show_column_menu(self.table.horizontalHeader().pos())

    def _toggle_column(self, col: int, visible: bool) -> None:
        self.table.setColumnHidden(col, not visible)
        self._save_column_state()

    def _reset_columns(self) -> None:
        for i in range(len(COLUMNS)):
            self.table.setColumnHidden(i, False)
        self.table.sortByColumn(-1, Qt.SortOrder.AscendingOrder)
        self._first_populate = True
        self._save_column_state()

    def _on_section_moved(self, logical: int, old_visual: int, new_visual: int) -> None:
        self._save_column_state()

    def _on_sort_changed(self, column: int, order) -> None:
        self._save_column_state()

    def _save_column_state(self) -> None:
        header = self.table.horizontalHeader()
        visible = [not self.table.isColumnHidden(i) for i in range(len(COLUMNS))]
        order = [header.visualIndex(i) for i in range(len(COLUMNS))]
        widths = [header.sectionSize(i) for i in range(len(COLUMNS))]
        self._settings.setValue(_SETTINGS_COL_VIS, json.dumps(visible))
        self._settings.setValue(_SETTINGS_COL_ORDER, json.dumps(order))
        self._settings.setValue(_SETTINGS_COL_WIDTHS, json.dumps(widths))
        sort_col = int(header.sortIndicatorSection())
        sort_ord = int(header.sortIndicatorOrder().value)
        self._settings.setValue(_SETTINGS_SORT, json.dumps([sort_col, sort_ord]))

    def _restore_column_state(self) -> None:
        vis_raw = self._settings.value(_SETTINGS_COL_VIS)
        if vis_raw:
            try:
                visible = json.loads(vis_raw)
                for i, v in enumerate(visible):
                    if i < len(COLUMNS):
                        self.table.setColumnHidden(i, not v)
            except (json.JSONDecodeError, TypeError):
                pass
        order_raw = self._settings.value(_SETTINGS_COL_ORDER)
        if order_raw:
            try:
                order = json.loads(order_raw)
                header = self.table.horizontalHeader()
                for logical, visual in enumerate(order):
                    if logical < len(COLUMNS):
                        header.moveSection(header.visualIndex(logical), visual)
            except (json.JSONDecodeError, TypeError):
                pass
        widths_raw = self._settings.value(_SETTINGS_COL_WIDTHS)
        if widths_raw:
            try:
                widths = json.loads(widths_raw)
                header = self.table.horizontalHeader()
                for i, w in enumerate(widths):
                    if i < len(COLUMNS) and w > 0:
                        header.resizeSection(i, w)
                self._first_populate = False
            except (json.JSONDecodeError, TypeError):
                pass
        sort_raw = self._settings.value(_SETTINGS_SORT)
        applied = False
        if sort_raw:
            try:
                sort_col, sort_ord = json.loads(sort_raw)
                if 0 <= sort_col < len(COLUMNS):
                    self.table.sortByColumn(
                        sort_col, Qt.SortOrder(sort_ord)
                    )
                    applied = True
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        if not applied:
            self.table.sortByColumn(1, Qt.SortOrder.AscendingOrder)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        self._save_column_state()
        super().closeEvent(event)

    # ---------------------------------------------------------- saved filters
    def _save_filter(self) -> None:
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Save filter", "Filter name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        presets = self._load_saved_filters()
        presets[name] = self._current_filters()
        self._settings.setValue(_SETTINGS_FILTERS, json.dumps(presets))
        self._refresh_saved_combo()

    def _load_saved_filters(self) -> dict:
        raw = self._settings.value(_SETTINGS_FILTERS)
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}

    def _refresh_saved_combo(self) -> None:
        self.saved_combo.blockSignals(True)
        self.saved_combo.clear()
        self.saved_combo.addItem("—", "")
        for name in self._load_saved_filters():
            self.saved_combo.addItem(name, name)
        self.saved_combo.blockSignals(False)

    def _recall_filter(self, _idx: int) -> None:
        name = self.saved_combo.currentData()
        if not name:
            return
        presets = self._load_saved_filters()
        f = presets.get(name)
        if not f:
            return
        self.search_edit.setText(f.get("search", ""))
        self._set_combo(self.group_combo, f.get("group", ""))
        self._set_combo(self.type_combo, f.get("type_", ""))
        self._set_combo(self.brand_combo, f.get("brand", ""))
        self._set_combo(self.status_combo, f.get("status", ""))
        self.refresh()

    @staticmethod
    def _set_combo(combo: QComboBox, value: str) -> None:
        idx = combo.findData(value)
        combo.setCurrentIndex(idx if idx >= 0 else 0)

    # ----------------------------------------------------------- recent files
    def _add_recent(self, key: str, path: str) -> None:
        recent = self._settings.value(key) or []
        if isinstance(recent, str):
            recent = [recent]
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:_MAX_RECENT]
        self._settings.setValue(key, recent)

    def _get_recent(self, key: str) -> list[str]:
        recent = self._settings.value(key) or []
        if isinstance(recent, str):
            recent = [recent]
        return [r for r in recent if r]

    def _refresh_recent_imports(self) -> None:
        self._refresh_recent_menu(self._imp_menu, _SETTINGS_RECENT_IMP, self._import_recent)

    def _refresh_recent_exports(self) -> None:
        self._refresh_recent_menu(self._exp_menu, _SETTINGS_RECENT_EXP, self._export_recent)

    def _refresh_recent_menu(self, menu: QMenu, key: str, slot) -> None:
        existing = menu.actions()
        for act in existing[3:]:
            menu.removeAction(act)
        recent = self._get_recent(key)
        if not recent:
            return
        sep = menu.addSeparator()
        sep.setParent(menu)
        for path in recent:
            act = QAction(Path(path).name, self)
            act.setToolTip(path)
            act.triggered.connect(lambda _checked, p=path: slot(p))
            menu.addAction(act)

    def _import_recent(self, path: str) -> None:
        if not Path(path).exists():
            QMessageBox.warning(self, "Recent file", f"File not found:\n{path}")
            return
        if path.endswith(config.ARCHIVE_EXT):
            self._run_import(lambda: import_archive(path), f"Restored from {Path(path).name}")
        elif path.endswith(".csv"):
            self._run_import(lambda: import_csv(path), f"Imported from {Path(path).name}")
        else:
            self._run_import(lambda: import_excel(path), f"Imported from {Path(path).name}")

    def _export_recent(self, path: str) -> None:
        if not Path(path).exists():
            QMessageBox.warning(self, "Recent file", f"Path not found:\n{path}")
            return
        label = "archive" if path.endswith(config.ARCHIVE_EXT) else (
            "CSV" if path.endswith(".csv") else "Excel"
        )
        self._run_export_path(path, label)

    # ------------------------------------------------------------- importers
    def _import_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Excel", "", "Excel (*.xlsx *.xlsm)"
        )
        if not path:
            return
        self._add_recent(_SETTINGS_RECENT_IMP, path)
        self._run_import(lambda: import_excel(path), f"Imported from {Path(path).name}")

    def _import_archive(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import archive", "",
            f"ThingKeeper archive (*{config.ARCHIVE_EXT});;All files (*.*)",
        )
        if not path:
            return
        self._add_recent(_SETTINGS_RECENT_IMP, path)
        self._run_import(lambda: import_archive(path), f"Restored from {Path(path).name}")

    def _import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "", "CSV (*.csv)"
        )
        if not path:
            return
        self._add_recent(_SETTINGS_RECENT_IMP, path)
        self._run_import(lambda: import_csv(path), f"Imported from {Path(path).name}")

    def _run_import(self, fn, success_title: str) -> None:
        try:
            result = fn()
        except Exception as exc:
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
        self._add_recent(_SETTINGS_RECENT_EXP, path)
        self._run_export(export_archive, path, "archive")

    def _export_excel(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Excel", "thingkeeper.xlsx", "Excel (*.xlsx)"
        )
        if not path:
            return
        self._add_recent(_SETTINGS_RECENT_EXP, path)
        self._run_export(export_excel, path, "Excel")

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "thingkeeper.csv", "CSV (*.csv)"
        )
        if not path:
            return
        self._add_recent(_SETTINGS_RECENT_EXP, path)
        self._run_export(export_csv, path, "CSV")

    def _export_html(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export HTML", "thingkeeper.html", "HTML (*.html *.htm)"
        )
        if not path:
            return
        self._add_recent(_SETTINGS_RECENT_EXP, path)
        self._run_export(export_html, path, "HTML")

    def _export_archive_encrypted(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export encrypted archive",
            "thingkeeper_encrypted" + config.ARCHIVE_EXT,
            f"Encrypted ThingKeeper archive (*{config.ARCHIVE_EXT})",
        )
        if not path:
            return
        passphrase, ok = QInputDialog.getText(
            self, "Passphrase",
            "Enter a passphrase for the encrypted archive:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not passphrase:
            return
        confirm, ok2 = QInputDialog.getText(
            self, "Confirm passphrase",
            "Re-enter the passphrase:",
            QLineEdit.EchoMode.Password,
        )
        if not ok2 or confirm != passphrase:
            QMessageBox.warning(self, "Encrypted export", "Passphrases do not match.")
            return
        self._add_recent(_SETTINGS_RECENT_EXP, path)
        try:
            export_archive_encrypted(path, passphrase)
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        QMessageBox.information(self, "Export", f"Encrypted archive saved to:\n{path}")

    def _import_archive_encrypted(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import encrypted archive", "",
            f"ThingKeeper archive (*{config.ARCHIVE_EXT});;All files (*.*)",
        )
        if not path:
            return
        if not is_encrypted_archive(path):
            QMessageBox.warning(
                self, "Encrypted import",
                "This file is not an encrypted ThingKeeper archive.\n"
                "Use the regular archive importer instead.",
            )
            return
        passphrase, ok = QInputDialog.getText(
            self, "Passphrase",
            "Enter the passphrase for this archive:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not passphrase:
            return
        self._add_recent(_SETTINGS_RECENT_IMP, path)
        self._run_import(
            lambda: import_archive_encrypted(path, passphrase),
            f"Restored from {Path(path).name}",
        )

    def _run_export(self, fn, path: str, label: str) -> None:
        try:
            fn(path)
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        QMessageBox.information(self, "Export", f"{label} saved to:\n{path}")

    def _run_export_path(self, path: str, label: str) -> None:
        fn = {
            "archive": export_archive,
            "CSV": export_csv,
            "Excel": export_excel,
            "HTML": export_html,
        }.get(label)
        if not fn:
            return
        try:
            fn(path)
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        QMessageBox.information(self, "Export", f"{label} saved to:\n{path}")

    # ------------------------------------------------------------------ misc
    def _about(self) -> None:
        QMessageBox.about(
            self, f"About {config.APP_NAME}",
            f"<h3>{config.APP_NAME} {config.APP_VERSION}</h3>"
            "<p>Desktop inventory app for gadgets, appliances and hardware parts.</p>"
            "<p>PyQt6 + SQLite. Proprietary license (© 2026 Stavros Antoniou).</p>"
        )

    # ----------------------------------------------------------- tools menu
    def backup_now(self) -> None:
        try:
            path = backup_mod.create_backup()
        except Exception as exc:
            QMessageBox.critical(self, "Backup failed", str(exc))
            return
        QMessageBox.information(
            self, "Backup",
            f"Backup created:\n{path}\n\n"
            f"Folder: {backup_mod.get_backup_dir()}",
        )

    def restore_from_backup(self) -> None:
        d = backup_mod.get_backup_dir()
        path, _ = QFileDialog.getOpenFileName(
            self, "Restore from backup", str(d),
            f"ThingKeeper archive (*{config.ARCHIVE_EXT})",
        )
        if not path:
            return
        confirm = QMessageBox.question(
            self, "Restore backup",
            f"Restore from {Path(path).name}?\n\n"
            "This will add items from the archive to the current inventory. "
            "Existing items are not removed.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._add_recent(_SETTINGS_RECENT_IMP, path)
        self._run_import(
            lambda: import_archive(path),
            f"Restored from {Path(path).name}",
        )

    def show_integrity(self) -> None:
        dlg = IntegrityDialog(self)
        dlg.exec()

    def show_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            self._backup_scheduler.restart()

    def _on_auto_backup(self, path: str) -> None:
        self.statusBar().showMessage(f"Auto-backup created: {path}", 5000)

    def _on_auto_backup_failed(self, msg: str) -> None:
        self.statusBar().showMessage(f"Auto-backup failed: {msg}", 8000)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.matches(QKeySequence.StandardKey.Find):
            self.search_edit.setFocus()
            self.search_edit.selectAll()
            return
        super().keyPressEvent(event)
