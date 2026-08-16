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

**Goal:** replace the original *My Equipment.xlsx* spreadsheet with a
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
- ~~**Crash reporting** — local-only log file the user can share on issue~~ (Deferred — see Long-term)
- **Test suite** — `tests/` with pytest + pytest-qt; 119 tests covering database,
  repository, importers, exporters, backup, integrity, commands, CLI, UI, theme
- **CI** — GitHub Actions (`.github/workflows/ci.yml`) running ruff + pytest on
  Ubuntu + Windows, Python 3.10 + 3.12

---

## Long-term ideas (Later)

- **Installer packages** — MSIX / Inno Setup on Windows, `.dmg` on macOS
- **Internationalisation** — extract strings, add Greek / English locales
- **In-app help** — first-launch tour, keyboard shortcut cheatsheet
- **Crash reporting** — local-only log file the user can share on issue
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
