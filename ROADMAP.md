# Roadmap

This document tracks the development direction of ThingKeeper. Items are
grouped by horizon, not by version. Priorities may shift based on real usage.

## Status legend

- **Done** — shipped in the current release
- **In progress** — actively being worked on
- **Planned** — next up, scoped but not started
- **Later** — under consideration, not committed
- **Dropped** — considered and rejected (with reason)

---

## v0.1 — Foundation (Done)

**Goal:** replace a personal inventory spreadsheet with a
maintainable desktop app.

- PyQt6 desktop UI (table, filters, search, status bar)
- SQLite storage with WAL mode (`thingkeeper/database.py`)
- Item model: group, type, brand, model, serial, store, purchase date,
  status, quantity, location, warranty end, notes, image attachment
- Full CRUD with validation (`thingkeeper/repository.py`)
- Status lifecycle: `AVAILABLE`, `IN USE`, `LOANED`, `BROKEN`, `SOLD`
- Warranty expiry highlighting (expired = red, expiring ≤30 days = amber)
- Image attachments stored under `data/attachments/`
- Import — Excel `.xlsx`, compressed JSON `.tkz`, CSV
- Export — `.tkz` (with attachments), CSV, Excel, PDF report
- Serial / barcode scan dialog (keyboard-wedge USB scanners)
- PDF inventory report (summary, by group, warranty alerts)
- Console-free launcher (`launch.pyw`) for Windows
- Proprietary license, README, ROADMAP, PROJECT_CONTEXT, AGENTS, requirements, pyproject

---

## v0.2 — Productivity (Done)

**Goal:** make daily use faster and more forgiving.

- **Undo / redo** for item edits and deletes (command pattern + history stack in `commands.py`)
- **Bulk edit** — change status / location / group for multiple selected items (`Ctrl+B`)
- **Duplicate item** — clone an existing item with a new serial (`Ctrl+D`)
- **Keyboard navigation** — `Delete`, `Ctrl+N`, `Ctrl+E`, `Ctrl+D`, `Ctrl+Z`, `Ctrl+Y` via `QAction` shortcuts
- **Column show/hide & ordering** — header right-click menu, drag-to-reorder, persisted via `QSettings`
- **Saved filters** — name and recall filter presets, stored as JSON in `QSettings`
- **Recent imports / exports** list in the File menu (last 8 each, `QSettings`)
- **Trash / soft delete** — `deleted_at` column, 30-day retention, `TrashDialog` for restore/purge
- **Multi-image attachments** — `item_images` table, gallery in `ItemDialog`, included in `.tkz` archives
- **Drag-and-drop** images onto an item dialog to attach
- **Date parsing tolerance** — `to_iso()` accepts `2024-03-26`, `26/03/2024`, `26.3.24`, `5-3-24`, `3/5/2024`
- **Minimal migration runner** — `schema_version` table + additive migrations (brought forward from v0.5)

---

## v0.3 — Loan tracking (Done)

**Goal:** know who has what, and when it should come back.

- **Loans table** — `loans(item_id, contact_id, borrower, loaned_on, due_on, returned_on, notes)` (migration v4)
- **Contacts table** — `contacts(name, phone, email, notes)` (migration v3)
- **Loan dialog** — pick a contact (or free-text borrower), due date, notes (`Ctrl+L`)
- **Return workflow** — one-click return from the Loans dialog, auto-stamps `returned_on`
- **Overdue highlighting** in the main table (red background on status cell) and Loans dialog
- **Loan history per item** — read-only `LoanHistoryDialog` accessible from the Loans menu
- **"On loan" status** auto-set when a loan opens; previous status restored on return
- **Loans overview dialog** — filter by open / overdue, return items inline
- **Contacts dialog** — search, add, edit, delete contacts
- **Archive format extended** — `.tkz` now includes loans + contacts (backward compatible with v0.2 archives)

---

## v0.4 — Reports & insights (Done)

**Goal:** turn the inventory into actionable knowledge.

- **Custom report builder** — choose columns, filters, grouping, sort, generate PDF (`File → Custom report builder`)
- **Dashboard** — bar chart of items per group, pie chart of status distribution, value-by-group bar chart, summary stats
- **Depreciation estimate** — straight-line depreciation based on purchase date + `depreciation_years` per item
- **Total value report** — `unit_price` field added (migration v5), sum of `quantity × unit_price` in PDF report + dashboard
- **Scheduled PDF export** — CLI entry point: `python -m thingkeeper --report PATH.pdf` (no GUI, schedulable via Task Scheduler / cron)
- **HTML export** — standalone `.html` file with styled table for easy sharing / printing

---

## v0.5 — Maintenance & resilience (Done)

**Goal:** keep data safe for the long term.

- **Automatic backup** — timestamped `.tkz` snapshots to a configurable folder;
  `BackupScheduler` runs at a user-set interval; `maybe_auto_backup()` on launch
- **Backup rotation** — keeps last N backups (default 10), prunes older
- **Backup manager** — `Tools → Back up now…` and `Tools → Restore from backup…`
- ~~**Schema migrations** — versioned `schema_version` table + migration runner~~ (Done in v0.2)
- **Data integrity check** — `Tools → Data integrity check…` detects orphan
  attachments, missing image files, orphan loan FK references
- **Attachment cleanup** — removes unreferenced files in `data/attachments/`;
  purges stale `item_images` rows; clears missing thumbnail paths
- **Encrypted archive export** — passphrase-protected `.tkz` using Fernet
  (SHA-256 derived key); `File → Export/Import → Encrypted archive`
- **Settings dialog** — `Tools → Settings…` for backup folder, retention count,
  auto-backup interval

---

## v1.0 — Hardening (Done)

**Goal:** first version that can be recommended to other people.

- **Cross-platform testing** — CI runs on Windows + Ubuntu; PyQt6 system deps
  installed on Linux
- ~~**Installer packages** — MSIX / Inno Setup on Windows, `.dmg` on macOS~~ (Deferred — see Long-term)
- ~~**Settings dialog** — data dir, backup folder, warranty soon-days, theme~~ (Done in v0.5; backup folder + retention + auto-backup interval)
- **Dark theme** — polished dark UI with Fusion style, accent highlights, and
  semantic colors (success/warning/danger/info); `theme.py` with QSS stylesheet;
  STATUS_COLORS centralized; applied unconditionally at startup
- ~~**Internationalisation** — extract strings, add Greek / English locales~~ (Deferred — see Long-term)
- **Accessibility pass** — status tips on all toolbar actions; accessible names
  and descriptions on search box + items table; keyboard shortcuts throughout
- ~~**In-app help** — first-launch tour, keyboard shortcut cheatsheet~~ (Deferred — see Long-term)
- ~~**Crash reporting** — local-only log file the user can share on issue~~ (Done in v1.2)
- **Test suite** — `tests/` with pytest + pytest-qt; 140 tests covering database,
  repository, importers, exporters, backup, integrity, commands, CLI, UI, theme,
  i18n, logging, and help
- **CI** — GitHub Actions (`.github/workflows/ci.yml`) running ruff + pytest on
  Ubuntu + Windows, Python 3.10 + 3.12

---

## v1.1 — UI polish (Done)

**Goal:** refine the day-to-day UX based on real usage of v1.0.

- **Fix: wrong item opened when table is sorted** — `_selected_items()` now
  reads the item ID from column 0's `UserRole` data and fetches by ID,
  instead of indexing `self._items` by visual row (which broke once the
  user clicked a column header to sort).
- **Date display** — Purchase and Warranty columns render as `DD-MM-YYYY`
  in the items table (stored as ISO `YYYY-MM-DD` in SQLite).
- **Auto-calculate warranty date** — changing the purchase date in the
  item dialog auto-fills the warranty end date to two years later
  (and enables "Has warranty") unless the user has already set a
  custom warranty date.
- **Smart warranty status indication** — the Warranty column now shows
  status at a glance via colour, weight, and a tooltip: no warranty
  (dim italic), expired (red bold on red bg, "Expired N… ago"), expires
  today (yellow bold), expiring soon ≤30 days (yellow, "N days left"),
  still valid (green, "Ny Ym left"). Computed inline per item; no extra
  DB queries on refresh.
- **Persistent table layout** — column widths, sort indicator
  (column + direction), visibility, and order persist across launches
  via `QSettings`. Auto-fit to content runs once on first launch, then
  widths are saved and restored.
- **All columns resizable** — every column (including Model) is in
  `Interactive` resize mode; the Model column is no longer locked to
  `Stretch`.
- **Centered numeric columns** — ID and Qty cells are centre-aligned.
- **Brighter scrollbar handles** — `#5a5a5a` default / `#707070` hover
  (was `#2a2a2a` / `#333333`, nearly invisible on the dark background).
- **README badges** — shields.io badges for CI, Python version, PyQt6,
  platform, test count, and license.

---

## v1.2 — Resilience, i18n, and in-app help (Done)

**Goal:** capture crashes in a local log file, translate the UI into
Greek and English, and add an in-app keyboard-shortcut cheatsheet and
first-launch tour.

- **Crash reporting (local log file)** — `thingkeeper/logging_config.py`
  configures a `RotatingFileHandler` (512 KB, 3 backups) at
  `data/thingkeeper.log` and installs a `sys.excepthook` so unhandled
  exceptions are captured with a full traceback before the app dies.
  `setup_logging()` runs at the very top of `app.run()` and
  `launch.pyw::_setup_logging()`; **Tools → Open log file** opens the
  log in the OS-default editor. `THINGKEEPER_DEBUG=1` enables debug
  level. The log file is git-ignored.
- **Internationalisation (Greek / English locales)** — new
  `thingkeeper/i18n.py` exposes `tr(text)`, `set_language(code)`,
  `get_language()`, and `available_languages()`. English is the
  source language (keys), Greek translations live in the `_EL` dict.
  The active language is persisted via `QSettings("ui/language")` and
  restored on next launch. **Settings → Language** dropdown switches
  between `en` (English) and `el` (Ελληνικά). All menu items, toolbar
  actions, filter labels, and the Settings/Help dialog strings are
  wrapped in `tr()`.
- **In-app help** — new `thingkeeper/ui/help_dialog.py`:
  - `ShortcutsDialog` — a 2-column table of all keyboard shortcuts
    (Ctrl+N, Ctrl+E, F1, etc.), bilingual content.
  - `TourDialog` — an 8-step first-launch tour with Previous/Next
    navigation and a progress indicator; bilingual content.
  - **Help → Keyboard shortcuts… (F1)** opens the cheatsheet.
  - **Help → First-launch tour…** replays the tour on demand.
- **Cross-platform builds** — `thingkeeper.spec` (PyInstaller) builds a
  onedir bundle with all assets bundled. `.github/workflows/release.yml`
  triggers on tag push (`v*`), builds two artifacts in parallel, and
  attaches them to a GitHub Release:
  - **Windows portable** — `ThingKeeper-v*.*.*-windows-portable.zip`
    (PyInstaller onedir, no installer needed, just unzip and run).
  - **Linux AppImage** — `ThingKeeper-v*.*.*-x86_64.AppImage`
    (PyInstaller + appimagetool, data stored in
    `~/.local/share/thingkeeper/` so it persists across updates).
- **Linux compatibility** — icon loading prefers PNG on non-Windows
  (`app.ico` on Windows, `icon.png` on Linux/macOS); all Windows API
  calls (`ctypes.windll`, `os.startfile`) are guarded by
  `sys.platform == "win32"`; `_open_log` uses `xdg-open` on Linux.

---

## Long-term ideas (Later)

- **Camera barcode scan** — use `python-opencv` or `zbar` for live camera decode
- **QR code labels** — generate printable QR labels per item/location
- **Multi-user sync** — optional sync to a remote folder (WebDAV / S3)
- **Companion mobile app** — read-only scan + lookup on Android via a small HTTP API
- **Network mode** — shared SQLite on NAS / SMB (caveats documented)
- **Plugin system** — Python entry points for custom importers / reports

---

## Dropped / not doing

- **Cloud SaaS** — out of scope; ThingKeeper is desktop-first and offline.
- **User accounts / auth** — single-user personal inventory by design.
- **Custom database backends** (Postgres/MySQL) — SQLite covers the use case
  and keeps deployment trivial.

---

## How to propose changes

Open an issue at <https://github.com/stavros-it/ThingKeeper/issues> with:

1. The use case you're trying to solve (not just the feature)
2. A sketch of the expected behaviour
3. Whether you'd be willing to implement it yourself

Small, well-scoped proposals are far more likely to land than sweeping rewrites.
