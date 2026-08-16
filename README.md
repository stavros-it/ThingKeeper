# ThingKeeper

A desktop inventory application for keeping track of gadgets, appliances, hardware
parts and anything else you own. Built with PyQt6 and SQLite — fast, offline, and
single-file storage.

## Features

- **Full CRUD** — add, edit, delete and browse inventory items.
- **Rich item model** — group, type, brand, model, serial, store, purchase date,
  status, quantity, location, warranty end date and free-form notes.
- **Status tracking** — `AVAILABLE`, `IN USE`, `LOANED`, `BROKEN`, `SOLD`.
- **Warranty & expiry** — items with an upcoming or expired warranty are flagged.
- **Image attachments** — attach a photo or receipt to any item.
- **Search & filter** — instant text search plus filters by group, type, brand and status.
- **Serial / barcode scan** — keyboard-wedge USB scanner support: focus the scan box,
  pull the trigger, and the matching item opens.
- **Import**
  - Excel workbook (`.xlsx`) — maps the original *My Equipment.xlsx* layout.
  - Compressed JSON archive (`.tkz`) — full backup including attachments.
  - CSV (`.csv`).
- **Export**
  - Compressed JSON archive (`.tkz`) — portable backup with attachments.
  - CSV (`.csv`).
  - Excel workbook (`.xlsx`).
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
| Edit item         | `Enter` / `Ctrl+E` |
| Delete item       | `Delete`        |
| Scan serial       | `Ctrl+K`        |
| Search            | `Ctrl+F`        |
| Refresh           | `F5`            |
| Quit              | `Ctrl+Q`        |

## Project layout

```
ThingKeeper/
├── main.py                 # entry point
├── thingkeeper/
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py           # paths & constants
│   ├── database.py         # SQLite connection + schema
│   ├── repository.py       # data access (CRUD + queries)
│   ├── importers.py        # xlsx / JSON / CSV import
│   ├── exporters.py        # JSON / CSV / xlsx / PDF export
│   ├── scanner.py          # serial-scan helper
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py
│       ├── item_dialog.py
│       ├── scan_dialog.py
│       └── reports_dialog.py
└── data/                   # runtime data (git-ignored)
    ├── thingkeeper.db
    └── attachments/
```

## License

MIT — see [LICENSE](LICENSE).
