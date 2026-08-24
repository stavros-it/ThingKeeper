# Project Context

This document is the single source of truth for what ThingKeeper is, how it's
built, and why decisions were made. New contributors (human or AI) should read
this before touching the codebase.

---

## 1. What is ThingKeeper?

ThingKeeper is a **desktop inventory application** for keeping track of
personal gadgets, appliances and hardware parts — the kind of thing most
people try to do with a sprawling Excel spreadsheet that stops scaling after
a few hundred rows.

It is **desktop-first**, **offline-first**, and **single-user** by design.
There is no cloud, no account, no sync server. The user's inventory lives in
one SQLite file plus an attachments folder on their own machine.

### Origin

The project was built to replace a personal inventory spreadsheet. The
expected Excel column layout is:

```
GROUP | TYPE | BRAND | MODEL | INFO | PURCHASE | SERIAL | STORE
```

Use **File → Import → Excel** to load any `.xlsx` file with these headers.
The original spreadsheet is deliberately git-ignored because it contains
the owner's personal inventory.

---

## 2. Tech stack and why

| Layer        | Choice              | Why |
|--------------|---------------------|-----|
| Language     | Python 3.10+        | Already known to the maintainer; rich ecosystem. |
| GUI toolkit  | PyQt6               | Mature, native-looking, well-documented, supports complex tables. |
| Storage      | SQLite (WAL mode)   | Zero-config, single file, transactional, more than fast enough for thousands of items. |
| Excel I/O    | openpyxl            | Pure-Python, no Excel install needed, matches the source spreadsheet format. |
| PDF reports  | reportlab          | De facto Python PDF library; flexible layout. |
| Images       | Pillow             | Already required by PyQt for some image paths; broadly useful. |
| Packaging    | pyproject.toml + setuptools | Standard Python packaging; `pip install -e .` works for dev. |

**Non-choices (intentional):**

- **No web framework** (Flask/FastAPI/Django). The user wanted a desktop app.
- **No ORM** (SQLAlchemy). The schema is small and stable; raw `sqlite3`
  keeps the dependency surface tiny and the SQL easy to audit.
- **No cloud / auth / multi-user.** Out of scope.

---

## 3. Architecture overview

```
                 ┌─────────────────────────┐
                 │       main.py           │  console entry
                 │       launch.pyw        │  no-console entry (Windows)
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   thingkeeper.app       │  QApplication bootstrap
                 └────────────┬────────────┘
                              │
            ┌─────────────────┴──────────────────┐
            │                                    │
            ▼                                    ▼
 ┌─────────────────────┐               ┌──────────────────────┐
 │  thingkeeper.ui     │  Qt widgets   │  thingkeeper.repo    │
 │  - main_window      │ ◀──────────── │  - Item dataclass    │
 │  - item_dialog      │               │  - CRUD + queries    │
 │  - scan_dialog      │               └──────────┬───────────┘
 │  - reports_dialog   │                          │
 └──────────┬──────────┘                          ▼
            │                          ┌──────────────────────┐
            ▼                          │  thingkeeper.database │  sqlite3
 ┌─────────────────────┐               │  - connect() / init  │
 │  thingkeeper.       │               │  - transaction()      │
 │    importers        │               └──────────┬───────────┘
 │    exporters        │                          │
 │    scanner          │                          ▼
 └──────────┬──────────┘               ┌──────────────────────┐
            │                          │  data/thingkeeper.db  │
            └─────────────────────────▶│  data/attachments/    │
                                       └──────────────────────┘
```

### Layering rules

- `database.py` knows only about `sqlite3` and `config`.
- `repository.py` depends on `database.py` and `config`. No Qt imports.
- `commands.py` depends on `repository.py`. No Qt imports.
- `importers.py` / `exporters.py` depend on `repository.py` and `config`.
  No Qt imports. (They may be imported from headless scripts.)
- `ui/*.py` depend on `repository.py`, `commands.py`, `importers.py`,
  `exporters.py`, `scanner.py`. No direct `sqlite3` use.
- `app.py` is the only module that constructs `QApplication`.

These rules keep the data layer unit-testable without a display server.

---

## 4. Data model

### `items` table

| Column          | Type     | Notes |
|-----------------|----------|-------|
| `id`            | INTEGER  | Primary key, autoincrement |
| `group_name`    | TEXT     | e.g. `IT`, `GADGET` (uppercase by convention) |
| `type`          | TEXT     | e.g. `smartphone`, `usb stick` (lowercase by convention) |
| `brand`         | TEXT     | e.g. `Motorola` |
| `model`         | TEXT     | free-form model string |
| `info`          | TEXT     | free-form notes / description |
| `serial`        | TEXT     | serial number or barcode value |
| `store`         | TEXT     | where it was bought |
| `purchase_date` | TEXT     | ISO `YYYY-MM-DD` (stored as text for portability) |
| `status`        | TEXT     | one of `config.STATUSES` |
| `quantity`      | INTEGER  | >= 1 |
| `location`      | TEXT     | room / shelf / box |
| `warranty_end`  | TEXT     | ISO date, empty if none |
| `image_path`    | TEXT     | absolute path under `data/attachments/` (primary image) |
| `unit_price`    | REAL     | purchase price per unit (optional, default 0.0) |
| `depreciation_years` | REAL | straight-line depreciation period in years (optional, default 0.0) |
| `deleted_at`    | TEXT     | non-null when soft-deleted (in trash); null otherwise |
| `created_at`    | TEXT     | `datetime('now')` |
| `updated_at`    | TEXT     | `datetime('now')`, refreshed on update |

**Indexes:** `group_name`, `type`, `brand`, `status`, `serial`, `deleted_at`.

### `item_images` table (multi-image, v0.2)

| Column       | Type     | Notes |
|--------------|----------|-------|
| `id`         | INTEGER  | Primary key, autoincrement |
| `item_id`    | INTEGER  | FK to `items(id)` ON DELETE CASCADE |
| `path`       | TEXT     | absolute path under `data/attachments/` |
| `kind`       | TEXT     | `'image'` (default) or `'receipt'`; v6 migration |
| `created_at` | TEXT     | `datetime('now')` |

**Index:** `item_id`.

The `kind` column (added in migration v6) lets the same table store both
gallery images and receipt/invoice files (including PDFs) without a
second table. Existing rows default to `'image'`, so historical data is
untouched. Receipts are excluded from `list_images()` / `set_images()`
and vice versa, so editing one kind never wipes the other.

### `schema_version` table (migration runner, v0.2)

| Column    | Type    | Notes |
|-----------|---------|-------|
| `version` | INTEGER | Primary key — the schema version reached |
| `applied` | TEXT    | `datetime('now')` — when the migration was applied |

The migration runner in `database.py` applies additive migrations in order
and records each applied version. Current schema version: 6.

### `contacts` table (loan tracking, v0.3)

| Column       | Type     | Notes |
|--------------|----------|-------|
| `id`         | INTEGER  | Primary key, autoincrement |
| `name`       | TEXT     | NOT NULL — full name |
| `phone`      | TEXT     | optional |
| `email`      | TEXT     | optional |
| `notes`      | TEXT     | free-form |
| `created_at` | TEXT     | `datetime('now')` |
| `updated_at` | TEXT     | `datetime('now')`, refreshed on update |

### `loans` table (loan tracking, v0.3)

| Column        | Type     | Notes |
|---------------|----------|-------|
| `id`          | INTEGER  | Primary key, autoincrement |
| `item_id`     | INTEGER  | FK to `items(id)` ON DELETE CASCADE |
| `contact_id`  | INTEGER  | FK to `contacts(id)` ON DELETE SET NULL |
| `borrower`    | TEXT     | NOT NULL — denormalised from contact for resilience |
| `loaned_on`   | TEXT     | ISO date, defaults to today |
| `due_on`      | TEXT     | ISO date, optional |
| `returned_on` | TEXT     | ISO date, NULL while loan is open |
| `notes`       | TEXT     | free-form |
| `created_at`  | TEXT     | `datetime('now')` |
| `updated_at`  | TEXT     | `datetime('now')`, refreshed on update |

**Indexes:** `item_id`, `contact_id`, `returned_on` (for fast "open loans" queries).

**Status lifecycle:** when `open_loan()` is called, the item's previous status
is stored as a marker in the `info` field (`[Previous status: AVAILABLE]`) and
the item's status is set to `LOANED`. On `return_loan()`, the marker is read
and stripped, and the item's status is restored. If no marker is found the
status defaults to `AVAILABLE`.

### Why dates are stored as TEXT

SQLite has no native DATE type. Storing ISO-8601 text keeps values sortable,
human-readable in `sqlite3` CLI, and trivially parseable by Python's
`date.fromisoformat()`. European formats (`DD/MM/YYYY`) are normalised to ISO
at import time by `repository.to_iso()`.

### Why the schema is in a single table

The original spreadsheet was flat and the use case is small. A single table
keeps queries, imports and exports simple. Future normalisation (loans,
contacts, categories) is planned in v0.3 — see [ROADMAP.md](ROADMAP.md).

---

## 5. File layout

```
ThingKeeper/
├── main.py                      # console entry point
├── launch.pyw                   # no-console entry point (Windows, double-click)
├── thingkeeper.spec             # PyInstaller spec (builds Windows + Linux binaries)
├── create_desktop_shortcut.bat  # installs a desktop shortcut with the app icon
├── packaging/                   # AppImage build assets
│   ├── thingkeeper.desktop      # Linux .desktop file
│   └── AppRun                   # AppImage entry point script
├── pyproject.toml               # packaging + ruff + pytest config
├── requirements.txt             # pinned runtime deps
├── README.md                    # user-facing docs
├── ROADMAP.md                   # development roadmap
├── PROJECT_CONTEXT.md           # this file
├── AGENTS.md                    # workflow + conventions for contributors
├── LICENSE                      # Proprietary
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml               # ruff + pytest on Ubuntu + Windows, Python 3.10 + 3.12
│       └── release.yml          # build Windows portable zip + Linux AppImage on tag push
├── tests/                       # pytest + pytest-qt test suite (140 tests)
└── thingkeeper/
    ├── __init__.py              # version
    ├── __main__.py              # python -m thingkeeper
    ├── app.py                   # QApplication bootstrap
    ├── config.py                # paths + constants
    ├── database.py              # sqlite3 connection + schema + migration runner
    ├── repository.py            # Item, Contact, Loan dataclasses + CRUD + queries
    ├── commands.py              # undo/redo command pattern + UndoStack
    ├── importers.py             # Excel / archive / CSV / encrypted archive import
    ├── exporters.py             # archive / CSV / Excel / HTML / PDF / encrypted archive export
    ├── backup.py                # timestamped backups + rotation + BackupScheduler
    ├── integrity.py             # data integrity check + orphan attachment cleanup
    ├── scanner.py              # serial lookup helper
    ├── logging_config.py        # RotatingFileHandler + sys.excepthook (crash log)
    ├── i18n.py                  # tr() function + Greek translations + language switcher
    ├── assets/
    │   ├── app.ico             # Windows icon (multi-size, used for shortcuts)
    │   ├── icon.png            # 512x512 PNG
    │   └── icon-256.png        # 256x256 PNG (README/docs)
    └── ui/
        ├── __init__.py
        ├── main_window.py       # table, filters, menus, toolbar, undo/redo, loans, contacts, dashboard, tools
        ├── item_dialog.py       # add/edit dialog (multi-image, price, depreciation, warranty)
        ├── bulk_edit_dialog.py  # bulk field change for selected items
        ├── loan_dialog.py       # open a loan for an item
        ├── loans_dialog.py      # browse open/all loans, return items
        ├── loan_history_dialog.py  # read-only loan history per item
        ├── contacts_dialog.py   # browse/add/edit/delete contacts
        ├── dashboard_dialog.py  # metric cards + bar charts + pie chart
        ├── report_builder_dialog.py  # custom PDF report builder
        ├── charts.py            # horizontal bar chart (QPainter) + pie chart (QPainter)
        ├── scan_dialog.py       # serial scan dialog
        ├── trash_dialog.py      # view / restore / purge soft-deleted items
        ├── integrity_dialog.py  # data integrity check + cleanup UI
        ├── settings_dialog.py   # backup folder, retention, auto-backup interval, language
        ├── help_dialog.py        # keyboard shortcut cheatsheet + first-launch tour
        ├── theme.py             # dark palette + QSS stylesheet + semantic colors
        ├── date_fmt.py          # OS regional date format helpers (QLocale.system())
        └── reports_dialog.py    # PDF report dialog
```

### Tests (`tests/`)

```
tests/
    ├── conftest.py            # fixtures: isolated data dir, offscreen Qt, fake QMessageBox
    ├── test_database.py       # schema, migrations, WAL, transaction
    ├── test_repository.py     # Item/Contact/Loan CRUD, aggregations, depreciation
    ├── test_importers.py      # Excel, CSV, archive, encrypted archive round-trips
    ├── test_exporters.py     # CSV, Excel, HTML, PDF, archive, encrypted
    ├── test_backup.py         # snapshots, rotation, auto-backup, BackupScheduler
    ├── test_integrity.py     # orphan detection, cleanup, stale image rows
    ├── test_commands.py       # undo/redo command pattern + UndoStack
    ├── test_cli.py            # `python -m thingkeeper --report PATH`
    ├── test_ui.py             # MainWindow + all dialogs (offscreen)
    ├── test_theme.py          # dark palette, styling, Fusion style
    ├── test_i18n.py           # tr(), language switching, Greek translations
    ├── test_logging.py        # RotatingFileHandler setup, excepthook
    └── test_help.py           # ShortcutsDialog + TourDialog (bilingual)
```

Run with `python -m pytest tests/ -q`.

### Runtime data (git-ignored)

```
data/
├── thingkeeper.db               # SQLite database (WAL mode)
├── thingkeeper.db-wal           # write-ahead log (auto-managed)
├── thingkeeper.db-shm          # shared memory (auto-managed)
└── attachments/                 # image files referenced by items
```

The `data/` location can be overridden with the `THINGKEEPER_DATA`
environment variable — useful for tests and for keeping the inventory on a
different drive / synced folder.

---

## 6. Key design decisions

### 6.1 Single-file storage, no server

SQLite with WAL mode gives concurrent reads while writing, survives crashes
better than default journal mode, and the database is one file you can copy
to back up. This matches the "personal spreadsheet replacement" goal.

### 6.2 Attachments are files, not BLOBs

Images go in `data/attachments/` with a UUID filename; the DB stores the path.
This keeps the DB small, lets users browse attachments directly, and makes
`.tkz` export trivial (zip the JSON manifest + the attachments folder).

### 6.3 The `.tkz` archive format

A `.tkz` file is a standard ZIP containing:

```
items.json.gz             # gzipped JSON array of item dicts
attachments/<file>        # image files
```

Gzipping the JSON before zipping gives much better compression for repetitive
text data, since ZIP's own DEFLATE doesn't re-compress already-compressed
payloads well. The format is open and documented; any user can unzip one.

### 6.4 Import is idempotent at the row level, not the item level

Importing the same `.xlsx` twice creates duplicate items. This was deliberate:
the source spreadsheet has no stable IDs, and deduplication by serial is
unreliable (many items have no serial). Users are expected to import once.
A future "deduplicate" tool may be added.

### 6.5 Barcode scanning assumes a keyboard wedge

No camera-based decoding is shipped. Most USB barcode scanners present as
keyboards: they type the code and press Enter. The scan dialog simply keeps
a `QLineEdit` focused and reacts to `returnPressed`. This keeps dependencies
at zero and supports every scanner on the market. Camera scanning is a
long-term idea in the roadmap.

### 6.6 Warranty status is computed at view time, per item

The main window computes warranty status inline for each item via
`_warranty_status()` in `main_window.py` during `_populate_table()`.
No separate `warranty_expired()` / `warranty_expiring()` queries are
issued on refresh — the status is derived from the item's
`warranty_end` ISO date and the current date. The result drives the
cell's foreground colour, background colour, font weight/italic, and
tooltip:

| State                         | Foreground | Background | Style      | Tooltip                        |
|-------------------------------|------------|------------|------------|--------------------------------|
| No warranty                   | dim        | —          | italic     | "No warranty"                  |
| Expired                       | red        | red bg     | bold       | "Expired N days/months/years ago" |
| Expires today                 | yellow     | yellow bg  | bold       | "Expires today"                |
| Expiring soon (≤30 days)      | yellow     | yellow bg  | normal     | "N days left"                  |
| Still valid                   | green      | —          | normal     | "Ny Ym left" / "Nm left"       |

Malformed dates fall back to plain text without crashing. Colours come
from `theme.py` (`SUCCESS`, `WARNING`, `DANGER`, `TEXT_DIM`, and their
`*_BG` counterparts) — never inlined.

### 6.7 Warranty auto-fill in the item dialog

When the purchase date changes in `ItemDialog`, the warranty end date
auto-fills to two years later (and checks "Has warranty") — but only if
the warranty is not yet enabled, or the warranty date still equals the
previous purchase date (i.e. the user hasn't customised it yet). A
manually-set warranty date is always preserved.

### 6.8 Dates are displayed with the OS regional format, stored as ISO

SQLite stores dates as ISO `YYYY-MM-DD` text (sortable, portable). The
items table renders them via the `_fmt_date()` helper in
`main_window.py`, which delegates to `thingkeeper/ui/date_fmt.py` and
`QLocale.system()`'s short date format. The item dialog and loan dialog
`QDateEdit` widgets use the same regional format via
`qt_date_format()`. Storage is always ISO — only display is localised.

### 6.9 Table layout persists across launches

Column visibility, order, widths, and the sort indicator (column +
direction) are persisted in `QSettings` and restored on startup. The
column widths are auto-fit to content once on the first populate after
launch (via `resizeColumnsToContents()`), then saved; on subsequent
launches the saved widths are restored and the auto-fit step is
skipped. "Reset to defaults" in the header context menu re-enables
auto-fit on the next refresh.

### 6.10 No background threads

Every operation (search, filter, import, export, PDF) runs on the UI thread.
For the expected dataset size (low thousands of items) this is snappy enough
that blocking is acceptable. If imports of tens of thousands of rows ever
become a real use case, a `QThread` worker should be introduced — but only
then; threading would complicate every import path for no current benefit.

### 6.11 Crash logging via RotatingFileHandler + excepthook

`thingkeeper/logging_config.py` configures a `RotatingFileHandler` (512 KB
per file, 3 backups) writing to `data/thingkeeper.log`, plus an
`sys.excepthook` override that logs any unhandled exception with a full
traceback at `CRITICAL` level before delegating to `sys.__excepthook__`.
`setup_logging()` is idempotent (guarded by a module-level `_installed`
flag) and is called at the very top of `app.run()` and again by
`launch.pyw::_setup_logging()` so the log captures both console and
no-console launch paths. `THINGKEEPER_DEBUG=1` enables `DEBUG` level.
The log file is git-ignored; users can open it via **Tools → Open log
file** which calls `os.startfile` (Windows), `open` (macOS), or
`xdg-open` (Linux).

### 6.12 Internationalisation is a Python dict, not gettext

`thingkeeper/i18n.py` provides a lightweight `tr(text)` function that
looks up the English source string in a `_EL` dict when the active
language is `el`; for `en` it returns the string unchanged. No `.po` /
`.mo` files, no `gettext` machinery — the table is small enough (~80
strings) to live in one Python file. The active language is persisted
in `QSettings("ui/language")` and restored on import via `_load_lang()`.
`set_language(code)` updates the in-memory `_LANG` and persists it.
Wrapping pattern: `from ..i18n import tr` then `tr("&File")` in any UI
code. Mnemonic markers (`&`) are preserved through the table so Qt
shortcuts keep working in both languages.

### 6.13 In-app help: shortcuts table + multi-step tour

`thingkeeper/ui/help_dialog.py` ships two dialogs, both bilingual:

- `ShortcutsDialog` — a 2-column `QTableWidget` of all keyboard
  shortcuts (Ctrl+N, Ctrl+E, F1, etc.). Content is hardcoded in
  `_SHORTCUTS_EN` / `_SHORTCUTS_EL` lists at module level (no DB).
- `TourDialog` — an 8-step first-launch tour with Previous/Next
  navigation and a "1 / 8" progress label. On the last step, the Next
  button is hidden and a Finish button appears. Content is in
  `_TOUR_STEPS_EN` / `_TOUR_STEPS_EL`.

Both are reachable from the **Help** menu: **Keyboard shortcuts… (F1)**
and **First-launch tour…**. The language is read at construction time
via `get_language()`, so the user gets the right locale by changing it
in Settings first.

### 6.14 Receipts / invoices share the item_images table via `kind`

Receipts and invoices (image or PDF) are stored in the same `item_images`
table as gallery images, distinguished by a `kind` column (`'image'`
default, `'receipt'` for receipts). Added in migration v6 with a
non-null default, so existing rows are auto-classified as images and
historical data is untouched.

- `repository.set_images()` writes only `kind='image'` rows; receipts
  are preserved when the user edits the gallery.
- `repository.set_receipts()` writes only `kind='receipt'` rows; images
  are preserved when the user edits receipts.
- `repository.duplicate_item()` copies both kinds so clones match.
- The `.tkz` archive serialises `extra_images` and `extra_receipts` as
  separate fields; import restores them with the right kind.
- The item dialog shows a "Receipt / Invoice" row with Attach / Open /
  Remove buttons. No in-app preview — "Open" launches the file via the
  OS default handler (`os.startfile` on Windows, `open` on macOS,
  `xdg-open` on Linux). PDFs and images both work because the file is
  just handed to the OS.
- `integrity.py` already iterates all `item_images` rows regardless of
  kind, so receipt orphans are detected and cleaned up automatically.

---

## 7. Conventions

### Code style

- Python 3.10+ syntax (PEP 604 unions, `match` allowed).
- Line length 100. Enforced via `ruff` (config in `pyproject.toml`).
- Linting: `ruff check .` must pass before commit.
- No type stubs for third-party libs required, but internal functions are
  type-annotated.
- Comments are sparse — the code should explain itself; the project context
  and roadmap carry the "why".

### Naming

- `group_name` column and `group` parameter (avoids the SQL reserved word
  `GROUP`).
- `type_` parameter in Python (avoids shadowing the builtin `type`).
- Status values are UPPERCASE strings, never enums (keeps them readable in
  the DB and in `sqlite3` CLI).

### Git

- Default branch: `main`.
- Commit messages: imperative mood, short subject, optional body
  explaining the *why*.
- Any personal inventory spreadsheets and `data/` are git-ignored.

---

## 8. How to run

```bash
# From the repo root
pip install -r requirements.txt
python main.py           # console entry
python launch.pyw        # Windows no-console entry (or double-click)
python -m thingkeeper    # equivalent to main.py
```

For headless / CI runs (e.g. smoke tests without a display):

```bash
# Linux / macOS
QT_QPA_PLATFORM=offscreen python main.py
# Windows (PowerShell)
$env:QT_QPA_PLATFORM='offscreen'; python main.py
```

### Run with a throwaway database

```bash
THINGKEEPER_DATA=/tmp/tk-test python main.py
```

Useful for reproducing a bug from scratch without touching your real
inventory.

---

## 9. Testing the data layer without Qt

Because `repository`, `importers` and `exporters` don't import Qt, they can
be exercised from a plain Python REPL:

```python
import os, tempfile
os.environ['THINGKEEPER_DATA'] = tempfile.mkdtemp()

import thingkeeper.config, thingkeeper.database, thingkeeper.importers
thingkeeper.database.init_db()
thingkeeper.importers.import_excel('your_inventory.xlsx')

from thingkeeper.repository import list_items
print(len(list_items()), 'items')
```

This is the pattern used by the smoke tests run during the initial build.

---

## 10. Where to make changes

| If you want to…                         | Touch… |
|-----------------------------------------|--------|
| Add a new item field                    | `repository.py` (dataclass + schema in `database.py` + importers/exporters + `item_dialog.py`) |
| Attach a receipt / invoice (image or PDF) | `item_dialog.py` Receipt section + `repository.set_receipts()` |
| Add a new filter                        | `repository.list_items()` + `main_window.py` |
| Add a new status                        | `config.STATUSES` + `theme.STATUS_COLORS` |
| Add a new import format                 | `importers.py` + a menu action in `main_window.py` |
| Add a new export format                 | `exporters.py` + a menu action in `main_window.py` |
| Change the DB schema                    | `database.py` migration function + bump `_SCHEMA_VERSION` |
| Change runtime paths                    | `config.py` |
| Change backup settings                  | `backup.py` (defaults) or `settings_dialog.py` (UI) |
| Add a new integrity check               | `integrity.py` + `integrity_dialog.py` |
| Add a keyboard shortcut                 | the relevant `QAction.setShortcut()` in `main_window.py` |
| Add a new report                        | `exporters.export_pdf_report()` or a sibling function + `reports_dialog.py` |
| Change warranty display logic           | `_warranty_status()` + `_fmt_date()` in `main_window.py` |
| Change date display format              | `thingkeeper/ui/date_fmt.py` (single source for `QLocale.system()`) |
| Change table column persistence        | `_save_column_state()` + `_restore_column_state()` in `main_window.py` |
| Add a new translation                   | add the English key + Greek value to `_EL` in `i18n.py`, then wrap the source string with `tr()` at the call site |
| Add a new language                      | add a `_XX` dict and a branch in `tr()` in `i18n.py`, plus the entry in `available_languages()` |
| Change log format / rotation size       | `logging_config.py` |
| Add a keyboard shortcut to cheatsheet   | `_SHORTCUTS_EN` + `_SHORTCUTS_EL` in `help_dialog.py` |
| Add or change a tour step               | `_TOUR_STEPS_EN` + `_TOUR_STEPS_EL` in `help_dialog.py` |

---

## 11. Known limitations

- No concurrency between processes — SQLite WAL allows one writer at a time.
  Running two instances on the same DB file simultaneously is unsupported.
- No bundled sample data — users import their own inventory via
  **File → Import → Excel**.

---

## 12. License

Proprietary (© 2026 Stavros Antoniou, all rights reserved). See [LICENSE](LICENSE).
