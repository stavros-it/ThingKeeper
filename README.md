# ThingKeeper

<p align="center">
  <img src="thingkeeper/assets/icon-256.png" alt="ThingKeeper icon" width="128" height="128">
</p>

<p align="center">
  <a href="https://github.com/stavros-it/ThingKeeper/actions/workflows/ci.yml"><img src="https://github.com/stavros-it/ThingKeeper/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/PyQt6-6.6+-41CD52?logo=qt&logoColor=white" alt="PyQt6 6.6+">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey" alt="Platform: Windows | Linux">
  <img src="https://img.shields.io/badge/Tests-120-brightgreen" alt="Tests: 120">
  <img src="https://img.shields.io/badge/License-Proprietary-red" alt="License: Proprietary">
</p>

A desktop inventory application for keeping track of gadgets, appliances, hardware
parts and anything else you own. Built with PyQt6 and SQLite — fast, offline, and
single-file storage.

## Features

- **Full CRUD** — add, edit, delete and browse inventory items.
- **Undo / redo** — every item operation is reversible (`Ctrl+Z` / `Ctrl+Y`).
- **Rich item model** — group, type, brand, model, serial, store, purchase date,
  status, quantity, location, warranty end date and free-form notes.
- **Status tracking** — `AVAILABLE`, `IN USE`, `LOANED`, `BROKEN`, `SOLD`.
- **Warranty & expiry** — items with an upcoming or expired warranty are flagged
  with colour-coded cells and tooltips ("Expired N days ago", "N days left",
  "Ny Ym left"). Warranty end auto-fills to 2 years after the purchase date
  when adding an item, and can be overridden for shorter/longer periods.
- **Multi-image attachments** — attach multiple photos/receipts per item;
  drag-and-drop directly onto the item dialog.
- **Bulk edit** — change a field (status, location, group…) across many items at once.
- **Duplicate item** — clone an existing item with one click (`Ctrl+D`).
- **Trash / soft delete** — deleted items go to trash, recoverable for 30 days.
- **Search & filter** — instant text search plus filters by group, type, brand and status.
- **Saved filter presets** — name and recall filter combinations.
- **Column show/hide & reorder** — right-click the table header, drag columns to reorder.
  Column widths, sort order, and visibility persist across launches.
- **Serial / barcode scan** — keyboard-wedge USB scanner support.
- **Loan tracking** — loan items to contacts, set due dates, one-click return;
  overdue loans are highlighted in the main table.
- **Contacts** — manage a list of contacts (name, phone, email, notes) for loans.
- **Loan history** — view the full loan history for any item.
- **Dashboard** — visual overview: bar charts by group, pie chart of status
  distribution, value summary, depreciation estimate.
- **Custom report builder** — choose columns, filters, grouping and sort to
  generate a custom PDF.
- **Depreciation tracking** — `unit_price` and `depreciation_years` fields per item;
  straight-line depreciation estimates in the dashboard and PDF report.
- **HTML export** — standalone HTML file for easy sharing and printing.
- **CLI report** — `python -m thingkeeper --report PATH.pdf` for scheduled PDF generation.
- **Automatic backups** — timestamped `.tkz` snapshots at a configurable interval,
  with rotation (keep last N). `Tools → Back up now` or `Tools → Restore from backup`.
- **Encrypted archives** — passphrase-protected `.tkz` using Fernet encryption
  for secure off-site backup.
- **Data integrity check** — `Tools → Data integrity check` detects orphan
  attachments, missing image files, and stale database rows; one-click cleanup.
- **Settings dialog** — `Tools → Settings` for backup folder, retention count,
  and auto-backup interval.
- **Dark theme** — polished dark UI with Fusion style, semantic colors, and
  accent highlights; applied unconditionally at startup via `theme.py`.
- **Test suite** — 120 pytest tests covering database, repository, importers,
  exporters, backup, integrity, commands, CLI, UI, and theme.
- **CI** — GitHub Actions runs ruff + pytest on every push (Ubuntu + Windows,
  Python 3.10 + 3.12).
- **Import** — Excel (`.xlsx`), compressed JSON archive (`.tkz`), CSV (`.csv`).
- **Export** — `.tkz` (with attachments), CSV, Excel, PDF report.
- **Recent files** — recently imported/exported files listed in the File menu.
- **Reports** — generate PDF inventory summaries (by group, status, expiring warranty).

## Install

```bash
git clone https://github.com/stavros-it/ThingKeeper.git
cd ThingKeeper
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

On Windows you can also double-click **`launch.pyw`** (or pin it to the
taskbar) — it uses `pythonw.exe`, so the app starts with no console window
in the background.

To create a **desktop shortcut** with the ThingKeeper icon, double-click
**`create_desktop_shortcut.bat`** (or run it from a terminal). It places a
`ThingKeeper.lnk` on the current user's desktop, pointing at `launch.pyw`
with `thingkeeper/assets/app.ico` as the icon.

On first launch ThingKeeper creates a SQLite database at `data/thingkeeper.db` and an
`data/attachments/` folder for images — both are git-ignored so your inventory stays
local and private.

## Importing your existing spreadsheet

Use **File → Import → Excel (.xlsx)** and pick your spreadsheet. The columns
`GROUP, TYPE, BRAND, MODEL, INFO, PURCHASE, SERIAL, STORE` are mapped automatically;
new fields default to sensible values (status `AVAILABLE`, quantity `1`).

## Keyboard shortcuts

| Action            | Shortcut        |
| ----------------- | --------------- |
| New item          | `Ctrl+N`        |
| Edit item         | `Ctrl+E`        |
| Duplicate item    | `Ctrl+D`        |
| Delete item       | `Delete`        |
| Undo              | `Ctrl+Z`        |
| Redo              | `Ctrl+Y`        |
| Bulk edit         | `Ctrl+B`        |
| Loan item         | `Ctrl+L`        |
| Generate report   | `Ctrl+R`        |
| Scan serial       | `Ctrl+K`        |
| Search            | `Ctrl+F`        |
| Refresh           | `F5`            |
| Quit              | `Ctrl+Q`        |

## Project layout

```
ThingKeeper/
├── main.py                 # entry point (console)
├── launch.pyw              # entry point (no console window on Windows, double-click)
├── create_desktop_shortcut.bat  # installs a desktop shortcut with the app icon
├── pyproject.toml          # packaging + ruff + pytest config
├── .github/workflows/
│   └── ci.yml              # ruff + pytest on Ubuntu + Windows
├── tests/                  # 120 pytest tests
└── thingkeeper/
    ├── __init__.py
    ├── __main__.py             # python -m thingkeeper [--report PATH]
    ├── config.py               # paths & constants
    ├── database.py             # SQLite connection + schema + migrations
    ├── repository.py           # data access (CRUD, multi-image, soft-delete, loans, contacts)
    ├── commands.py             # undo/redo command pattern + UndoStack
    ├── importers.py            # xlsx / .tkz / CSV / encrypted archive import
    ├── exporters.py            # .tkz / CSV / xlsx / HTML / PDF / encrypted archive export
    ├── backup.py               # timestamped backups + rotation + BackupScheduler
    ├── integrity.py            # data integrity check + orphan attachment cleanup
    ├── scanner.py              # serial-scan helper
    ├── assets/
    │   ├── app.ico             # Windows icon (multi-size)
    │   ├── icon.png            # 512x512 PNG icon
    │   └── icon-256.png        # 256x256 PNG (for README/docs)
    └── ui/
        ├── __init__.py
        ├── main_window.py           # table, filters, toolbar, undo/redo, saved filters
        ├── item_dialog.py           # add/edit (multi-image, price, depreciation)
        ├── bulk_edit_dialog.py      # bulk field change
        ├── loan_dialog.py           # open a loan for an item
        ├── loans_dialog.py          # browse loans, return items
        ├── loan_history_dialog.py   # loan history per item
        ├── contacts_dialog.py       # manage contacts
        ├── dashboard_dialog.py      # charts + summary stats
        ├── report_builder_dialog.py # custom PDF report builder
        ├── charts.py                # bar chart (pyqtgraph) + pie chart (QPainter)
        ├── scan_dialog.py           # serial scan
        ├── trash_dialog.py          # view / restore / purge deleted items
        ├── integrity_dialog.py      # data integrity check + cleanup UI
        ├── settings_dialog.py       # backup folder, retention, auto-backup interval
        ├── theme.py                 # dark palette + QSS stylesheet + semantic colors
        └── reports_dialog.py        # PDF report
└── data/                   # runtime data (git-ignored)
    ├── thingkeeper.db
    └── attachments/
```

## License

Proprietary (© 2026 Stavros Antoniou, all rights reserved) — see [LICENSE](LICENSE).

## AI assistance

Parts of this codebase, documentation and commit messages were generated
or refined with the help of AI tools. All output was reviewed and accepted
by the maintainer before being committed.

## Project docs

- [AGENTS.md](AGENTS.md) — workflow and conventions for AI assistants and contributors.
- [ROADMAP.md](ROADMAP.md) — what's shipped, what's planned, what's dropped.
- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) — architecture, data model and
  design decisions for contributors.
