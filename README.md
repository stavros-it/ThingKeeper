# ThingKeeper

A desktop inventory application for keeping track of gadgets, appliances, hardware
parts and anything else you own. Built with PyQt6 and SQLite — fast, offline, and
single-file storage.

## Features

- **Full CRUD** — add, edit, delete and browse inventory items.
- **Undo / redo** — every item operation is reversible (`Ctrl+Z` / `Ctrl+Y`).
- **Rich item model** — group, type, brand, model, serial, store, purchase date,
  status, quantity, location, warranty end date and free-form notes.
- **Status tracking** — `AVAILABLE`, `IN USE`, `LOANED`, `BROKEN`, `SOLD`.
- **Warranty & expiry** — items with an upcoming or expired warranty are flagged.
- **Multi-image attachments** — attach multiple photos/receipts per item;
  drag-and-drop directly onto the item dialog.
- **Bulk edit** — change a field (status, location, group…) across many items at once.
- **Duplicate item** — clone an existing item with one click (`Ctrl+D`).
- **Trash / soft delete** — deleted items go to trash, recoverable for 30 days.
- **Search & filter** — instant text search plus filters by group, type, brand and status.
- **Saved filter presets** — name and recall filter combinations.
- **Column show/hide & reorder** — right-click the table header, drag columns to reorder.
- **Serial / barcode scan** — keyboard-wedge USB scanner support.
- **Loan tracking** — loan items to contacts, set due dates, one-click return;
  overdue loans are highlighted in the main table.
- **Contacts** — manage a list of contacts (name, phone, email, notes) for loans.
- **Loan history** — view the full loan history for any item.
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

On first launch ThingKeeper creates a SQLite database at `data/thingkeeper.db` and an
`data/attachments/` folder for images — both are git-ignored so your inventory stays
local and private.

## Importing your existing spreadsheet

Use **File → Import → Excel (.xlsx)** and pick your `My Equipment.xlsx`. The columns
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
| Scan serial       | `Ctrl+K`        |
| Search            | `Ctrl+F`        |
| Generate report   | `Ctrl+R`        |
| Refresh           | `F5`            |
| Quit              | `Ctrl+Q`        |

## Project layout

```
ThingKeeper/
├── main.py                 # entry point (console)
├── launch.pyw              # entry point (no console window on Windows)
├── thingkeeper/
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py           # paths & constants
│   ├── database.py         # SQLite connection + schema + migrations
│   ├── repository.py       # data access (CRUD, multi-image, soft-delete)
│   ├── commands.py         # undo/redo command pattern + UndoStack
│   ├── importers.py        # xlsx / .tkz / CSV import
│   ├── exporters.py        # .tkz / CSV / xlsx / PDF export
│   ├── scanner.py          # serial-scan helper
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py       # table, filters, toolbar, undo/redo, saved filters
│       ├── item_dialog.py       # add/edit (multi-image gallery + drag-and-drop)
│       ├── bulk_edit_dialog.py  # bulk field change
│       ├── loan_dialog.py       # open a loan for an item
│       ├── loans_dialog.py      # browse loans, return items
│       ├── loan_history_dialog.py  # loan history per item
│       ├── contacts_dialog.py   # manage contacts
│       ├── scan_dialog.py       # serial scan
│       ├── trash_dialog.py      # view / restore / purge deleted items
│       └── reports_dialog.py    # PDF report
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
