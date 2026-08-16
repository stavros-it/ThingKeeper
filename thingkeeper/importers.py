"""Importers: Excel (.xlsx), compressed JSON archive (.tkz), CSV."""

from __future__ import annotations

import csv
import gzip
import json
import shutil
import zipfile
from pathlib import Path

from . import config
from .repository import Item, bulk_insert, to_iso

# Column header -> item field mapping for Excel import.
EXCEL_HEADER_MAP = {
    "GROUP": "group_name",
    "TYPE": "type",
    "BRAND": "brand",
    "MODEL": "model",
    "INFO": "info",
    "PURCHASE": "purchase_date",
    "PURCHASE_DATE": "purchase_date",
    "SERIAL": "serial",
    "STORE": "store",
    "STATUS": "status",
    "QUANTITY": "quantity",
    "QTY": "quantity",
    "LOCATION": "location",
    "WARRANTY_END": "warranty_end",
    "WARRANTY": "warranty_end",
    "UNIT_PRICE": "unit_price",
    "PRICE": "unit_price",
    "DEPRECIATION_YEARS": "depreciation_years",
    "DEPRECIATION": "depreciation_years",
}


class ImportResult:
    """Outcome of an import operation."""

    def __init__(self, imported: int, skipped: int, errors: list[str] | None = None):
        self.imported = imported
        self.skipped = skipped
        self.errors = errors or []

    def __repr__(self) -> str:
        return (
            f"ImportResult(imported={self.imported}, "
            f"skipped={self.skipped}, errors={len(self.errors)})"
        )


def _clean(value):
    """Strip whitespace from strings; pass through dates/datetimes unchanged
    so that to_iso() can handle them properly."""
    from datetime import date, datetime

    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value
    return str(value).strip()


def import_excel(path: str | Path) -> ImportResult:
    """Import items from an .xlsx workbook."""
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    try:
        header = [str(c).strip().upper() if c is not None else "" for c in next(rows)]
    except StopIteration:
        return ImportResult(0, 0, ["Workbook is empty"])

    # Build index of recognised columns.
    col_map: dict[int, str] = {}
    for idx, head in enumerate(header):
        if head in EXCEL_HEADER_MAP:
            col_map[idx] = EXCEL_HEADER_MAP[head]

    items: list[Item] = []
    skipped = 0
    errors: list[str] = []
    for rno, row in enumerate(rows, start=2):
        # Skip fully-blank rows.
        if not any(c is not None and str(c).strip() != "" for c in row):
            skipped += 1
            continue
        record: dict[str, str] = {}
        for idx, field in col_map.items():
            if idx < len(row):
                record[field] = _clean(row[idx])
        # Skip if no identifying info at all.
        if not any(record.get(f) for f in ("brand", "model", "serial", "info")):
            skipped += 1
            continue
        try:
            items.append(_record_to_item(record))
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(f"Row {rno}: {exc}")
            skipped += 1

    imported = bulk_insert(items)
    return ImportResult(imported, skipped, errors)


def _record_to_item(record: dict) -> Item:
    def _float(val, default=0.0) -> float:
        try:
            return float(val) if val not in (None, "") else default
        except (ValueError, TypeError):
            return default

    return Item(
        id=None,
        group_name=str(record.get("group_name", "")),
        type=str(record.get("type", "")),
        brand=str(record.get("brand", "")),
        model=str(record.get("model", "")),
        info=str(record.get("info", "")),
        serial=str(record.get("serial", "")),
        store=str(record.get("store", "")),
        purchase_date=to_iso(record.get("purchase_date", "")),
        status=str(record.get("status", config.DEFAULT_STATUS)).upper()
        or config.DEFAULT_STATUS,
        quantity=int(record.get("quantity", 1) or 1),
        location=str(record.get("location", "")),
        warranty_end=to_iso(record.get("warranty_end", "")),
        image_path="",  # attachments restored separately
        unit_price=_float(record.get("unit_price", 0.0)),
        depreciation_years=_float(record.get("depreciation_years", 0.0)),
    )


def import_archive(path: str | Path) -> ImportResult:
    """Import a .tkz (zip + gzip json + attachments) archive.

    Supports two layouts:
    - v0.2 (legacy): items.json.gz contains a JSON list of item dicts.
    - v0.3+: items.json.gz contains {"items": [...], "loans": [...], "contacts": [...]}.

    Attachments are restored under data/attachments/.
    """
    path = Path(path)
    errors: list[str] = []
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()
        if "items.json.gz" not in names:
            return ImportResult(0, 0, ["Archive is missing items.json.gz"])
        with zf.open("items.json.gz") as raw:
            payload = gzip.decompress(raw.read())
        try:
            data = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:
            return ImportResult(0, 0, [f"Invalid JSON: {exc}"])

        # Normalise to dict-with-sections; old archives are a bare list.
        if isinstance(data, list):
            item_records = data
            loan_records: list[dict] = []
            contact_records: list[dict] = []
        else:
            item_records = data.get("items", [])
            loan_records = data.get("loans", [])
            contact_records = data.get("contacts", [])

        items = []
        for i, record in enumerate(item_records, start=1):
            try:
                items.append(_record_to_item(record))
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(f"Item {i}: {exc}")

        # Restore attachment files.
        restored = 0
        for name in names:
            if name.startswith("attachments/") and not name.endswith("/"):
                target = config.ATTACHMENTS_DIR / Path(name).name
                with zf.open(name) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                restored += 1
        # Re-attach image paths now that files exist.
        attach_names = {
            Path(n).name for n in names if n.startswith("attachments/")
        }
        extra_to_restore: list[tuple[int, list[str]]] = []
        for idx, (record, item) in enumerate(zip(item_records, items)):
            img = record.get("image_path") or ""
            if img:
                base = Path(img).name
                if base in attach_names:
                    item.image_path = str(config.ATTACHMENTS_DIR / base)
            extras = record.get("extra_images") or []
            if extras and item.id is None:
                extra_to_restore.append((idx, [
                    str(config.ATTACHMENTS_DIR / Path(e).name)
                    for e in extras if Path(e).name in attach_names
                ]))

        imported = bulk_insert(items)
        # Now that items have IDs, restore extra images.
        from .repository import add_image  # local to avoid cycle at import time
        for idx, paths in extra_to_restore:
            if idx < len(items) and items[idx].id is not None:
                for p in paths:
                    add_image(items[idx].id, p)

        # Restore contacts (must come before loans so FK can resolve).
        contact_id_map: dict[int, int] = {}
        from .repository import Contact, create_contact
        for record in contact_records:
            old_id = record.get("id")
            contact = Contact(
                name=str(record.get("name", "")),
                phone=str(record.get("phone", "")),
                email=str(record.get("email", "")),
                notes=str(record.get("notes", "")),
            )
            new_id = create_contact(contact)
            if old_id is not None:
                contact_id_map[int(old_id)] = new_id

        # Restore loans. We re-map item_id by serial if possible,
        # otherwise by matching brand+model. Falls back to skipping.
        from .repository import find_by_serial, open_loan
        for record in loan_records:
            borrower = str(record.get("borrower", "")).strip()
            if not borrower:
                errors.append("Loan skipped: no borrower")
                continue
            old_contact_id = record.get("contact_id")
            due_on = str(record.get("due_on", "") or "")
            notes = str(record.get("notes", "") or "")
            # Try to find the item by serial first; this is best-effort.
            item = None
            serial = record.get("_serial", "")
            if serial:
                item = find_by_serial(str(serial))
            if item is None:
                errors.append(f"Loan for borrower '{borrower}' skipped: item not found")
                continue
            new_contact_id = contact_id_map.get(int(old_contact_id)) if old_contact_id else None
            try:
                open_loan(
                    item.id,
                    borrower=borrower,
                    contact_id=new_contact_id,
                    due_on=due_on,
                    notes=notes,
                )
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(f"Loan for '{borrower}': {exc}")

        return ImportResult(imported, 0, errors)


# CSV column aliases (case-insensitive) -> item field.
_CSV_ALIASES = {
    "group": "group_name",
    "group_name": "group_name",
    "type": "type",
    "brand": "brand",
    "model": "model",
    "info": "info",
    "notes": "info",
    "description": "info",
    "purchase": "purchase_date",
    "purchase_date": "purchase_date",
    "serial": "serial",
    "serial_number": "serial",
    "store": "store",
    "status": "status",
    "quantity": "quantity",
    "qty": "quantity",
    "location": "location",
    "warranty_end": "warranty_end",
    "warranty": "warranty_end",
    "unit_price": "unit_price",
    "price": "unit_price",
    "depreciation_years": "depreciation_years",
    "depreciation": "depreciation_years",
}


def import_csv(path: str | Path) -> ImportResult:
    """Import items from a CSV file. Header row required."""
    items: list[Item] = []
    skipped = 0
    errors: list[str] = []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        try:
            header = [h.strip().lower() for h in next(reader)]
        except StopIteration:
            return ImportResult(0, 0, ["CSV is empty"])
        col_map: dict[int, str] = {}
        for idx, head in enumerate(header):
            if head in _CSV_ALIASES:
                col_map[idx] = _CSV_ALIASES[head]
        if not col_map:
            return ImportResult(0, 0, ["No recognised columns in CSV header"])

        for rno, row in enumerate(reader, start=2):
            if not any(c.strip() for c in row):
                skipped += 1
                continue
            record: dict[str, str] = {}
            for idx, field in col_map.items():
                if idx < len(row):
                    record[field] = row[idx].strip()
            try:
                items.append(_record_to_item(record))
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(f"Row {rno}: {exc}")
                skipped += 1

    imported = bulk_insert(items)
    return ImportResult(imported, skipped, errors)


def import_archive_encrypted(path: str | Path, passphrase: str) -> ImportResult:
    """Import a passphrase-encrypted .tkz archive.

    Decrypts to a temporary plain archive, then delegates to import_archive.
    """
    import tempfile

    from cryptography.fernet import Fernet

    from .exporters import _ENC_MAGIC, _derive_key

    if not passphrase:
        return ImportResult(0, 0, ["Passphrase is required"])
    with open(path, "rb") as f:
        magic = f.read(len(_ENC_MAGIC))
        if magic != _ENC_MAGIC:
            return ImportResult(0, 0, ["File is not an encrypted archive"])
        token = f.read()
    try:
        data = Fernet(_derive_key(passphrase)).decrypt(token)
    except Exception:
        return ImportResult(0, 0, ["Wrong passphrase or corrupted file"])
    with tempfile.NamedTemporaryFile(
        suffix=config.ARCHIVE_EXT, delete=False
    ) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        return import_archive(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
