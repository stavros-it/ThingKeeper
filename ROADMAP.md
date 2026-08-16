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

## v0.4 — Reports & insights (Planned)

**Goal:** turn the inventory into actionable knowledge.

- **Custom report builder** — choose columns, filters, grouping, sort
- **Charts** — bar chart of items per group, pie of status distribution
- **Depreciation estimate** — based on purchase date + category lifespan
- **Total value report** — sum `quantity × unit_price` (new optional field)
- **Scheduled PDF export** — monthly snapshot to a chosen folder
- **HTML export** for easy sharing / printing

---

## v0.5 — Maintenance & resilience (Later)

**Goal:** keep data safe for the long term.

- **Automatic backup** — daily `.tkz` snapshot to a configurable folder
- **Backup rotation** — keep last N backups, prune older
- ~~**Schema migrations** — versioned `schema_version` table + migration runner~~ (Done in v0.2)
- **Data integrity check** — Tools → Verify database (orphan attachments, etc.)
- **Attachment cleanup** — remove image files no longer referenced by any item
- **Encrypted archive export** — optional passphrase-protected `.tkz`

---

## v1.0 — Hardening (Later)

**Goal:** first version that can be recommended to other people.

- **Cross-platform testing** — Windows, macOS, Linux
- **Installer packages** — MSIX / Inno Setup on Windows, `.dmg` on macOS
- **Settings dialog** — data dir, backup folder, warranty soon-days, theme
- **Dark mode** — follow system palette
- **Internationalisation** — extract strings, add Greek / English locales
- **Accessibility pass** — keyboard-only navigation, screen reader labels
- **In-app help** — first-launch tour, keyboard shortcut cheatsheet
- **Crash reporting** — local-only log file the user can share on issue
- **Test suite** — `tests/` with pytest, mocked DB for unit tests
- **CI** — GitHub Actions running ruff + pytest on every push

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
