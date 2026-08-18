"""Data access layer: CRUD, filtering, soft-delete, multi-image and aggregation."""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from . import config
from .database import connect


@dataclass(slots=True)
class Item:
    id: int | None = None
    group_name: str = ""
    type: str = ""
    brand: str = ""
    model: str = ""
    info: str = ""
    serial: str = ""
    store: str = ""
    purchase_date: str = ""
    status: str = config.DEFAULT_STATUS
    quantity: int = 1
    location: str = ""
    warranty_end: str = ""
    image_path: str = ""
    unit_price: float = 0.0
    depreciation_years: float = 0.0
    deleted_at: str = ""
    created_at: str = ""
    updated_at: str = ""

    COLUMNS: tuple = field(default_factory=lambda: (
        "group_name", "type", "brand", "model", "info", "serial",
        "store", "purchase_date", "status", "quantity", "location",
        "warranty_end", "image_path", "unit_price", "depreciation_years",
    ))

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Item:
        return cls(
            id=row["id"],
            group_name=row["group_name"] or "",
            type=row["type"] or "",
            brand=row["brand"] or "",
            model=row["model"] or "",
            info=row["info"] or "",
            serial=row["serial"] or "",
            store=row["store"] or "",
            purchase_date=row["purchase_date"] or "",
            status=row["status"],
            quantity=row["quantity"],
            location=row["location"] or "",
            warranty_end=row["warranty_end"] or "",
            image_path=row["image_path"] or "",
            unit_price=row["unit_price"] if row["unit_price"] is not None else 0.0,
            depreciation_years=(
                row["depreciation_years"]
                if row["depreciation_years"] is not None
                else 0.0
            ),
            deleted_at=row["deleted_at"] or "",
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
        )

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "group_name": self.group_name,
            "type": self.type,
            "brand": self.brand,
            "model": self.model,
            "info": self.info,
            "serial": self.serial,
            "store": self.store,
            "purchase_date": self.purchase_date,
            "status": self.status,
            "quantity": self.quantity,
            "location": self.location,
            "warranty_end": self.warranty_end,
            "image_path": self.image_path,
            "unit_price": self.unit_price,
            "depreciation_years": self.depreciation_years,
            "deleted_at": self.deleted_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


_DATE_FORMATS = (
    "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
    "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
    "%m/%d/%Y", "%m-%d-%Y",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
)
_DMY_RE = re.compile(r"^(\d{1,2})\D(\d{1,2})\D(\d{2,4})$")
_YMD_RE = re.compile(r"^(\d{4})\D(\d{1,2})\D(\d{1,2})$")


def to_iso(value) -> str:
    """Normalise various date formats into ISO (YYYY-MM-DD). Empty stays empty."""
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    s = str(value).strip()
    if not s:
        return ""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    # Tolerate 1-2 digit day/month and 2-digit years: 26.3.24, 5/3/2024
    m = _YMD_RE.match(s) or _DMY_RE.match(s)
    if m:
        parts = [int(p) for p in m.groups()]
        if len(str(m.group(1))) == 4:
            y, mo, d = parts
        else:
            d, mo, y = parts
            if y < 100:
                y += 2000 if y < 70 else 1900
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            pass
    return s


def create_item(item: Item) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO items
                (group_name, type, brand, model, info, serial, store,
                 purchase_date, status, quantity, location, warranty_end,
                 image_path, unit_price, depreciation_years)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                item.group_name, item.type, item.brand, item.model, item.info,
                item.serial, item.store, item.purchase_date, item.status,
                item.quantity, item.location, item.warranty_end,
                item.image_path, item.unit_price, item.depreciation_years,
            ),
        )
        conn.commit()
        item.id = int(cur.lastrowid)
        return item.id


def update_item(item: Item) -> None:
    if item.id is None:
        raise ValueError("Item id is required for update")
    with connect() as conn:
        conn.execute(
            """
            UPDATE items SET
                group_name=?, type=?, brand=?, model=?, info=?, serial=?, store=?,
                purchase_date=?, status=?, quantity=?, location=?, warranty_end=?,
                image_path=?, unit_price=?, depreciation_years=?,
                updated_at=datetime('now')
            WHERE id=?
            """,
            (
                item.group_name, item.type, item.brand, item.model, item.info,
                item.serial, item.store, item.purchase_date, item.status,
                item.quantity, item.location, item.warranty_end,
                item.image_path, item.unit_price, item.depreciation_years,
                item.id,
            ),
        )
        conn.commit()


def bulk_update(item_ids: Iterable[int], fields: dict) -> None:
    """Apply the same field updates to many items at once.

    `fields` maps column names to their new values. Only editable text/integer
    columns are allowed.
    """
    allowed = {
        "group_name", "type", "brand", "store", "location", "status",
        "purchase_date", "warranty_end", "unit_price", "depreciation_years",
    }
    bad = set(fields) - allowed
    if bad:
        raise ValueError(f"Cannot bulk-update columns: {bad}")
    if not fields or not item_ids:
        return
    ids = list(item_ids)
    assignments = ", ".join(f"{col}=?" for col in fields)
    params = list(fields.values()) + ids
    placeholders = ",".join("?" * len(ids))
    sql = (
        f"UPDATE items SET {assignments}, updated_at=datetime('now') "
        f"WHERE id IN ({placeholders})"
    )
    with connect() as conn:
        conn.execute(sql, params)
        conn.commit()


def soft_delete(item_id: int) -> None:
    """Move an item to trash (sets deleted_at). Recoverable via restore_item."""
    with connect() as conn:
        conn.execute(
            "UPDATE items SET deleted_at=datetime('now') WHERE id=?", (item_id,)
        )
        conn.commit()


def restore_item(item_id: int) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE items SET deleted_at=NULL WHERE id=?", (item_id,)
        )
        conn.commit()


def hard_delete(item_id: int) -> None:
    """Permanently delete an item and its images. Cannot be undone."""
    with connect() as conn:
        conn.execute("DELETE FROM item_images WHERE item_id=?", (item_id,))
        conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit()


def delete_item(item_id: int) -> None:
    """Default delete = soft delete (recoverable from trash for 30 days)."""
    soft_delete(item_id)


def purge_old_trash(days: int = 30) -> int:
    """Permanently delete items that have been in trash longer than `days`.

    Returns the number of items purged.
    """
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    with connect() as conn:
        rows = conn.execute(
            "SELECT id FROM items WHERE deleted_at IS NOT NULL AND deleted_at < ?",
            (cutoff,),
        ).fetchall()
        ids = [r["id"] for r in rows]
        if ids:
            placeholders = ",".join("?" * len(ids))
            conn.execute(
                f"DELETE FROM item_images WHERE item_id IN ({placeholders})", ids
            )
            conn.execute(f"DELETE FROM items WHERE id IN ({placeholders})", ids)
        conn.commit()
    return len(ids)


def get_item(item_id: int) -> Item | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return Item.from_row(row) if row else None


def find_by_serial(serial: str) -> Item | None:
    """Return the first non-deleted item whose serial matches."""
    s = (serial or "").strip()
    if not s:
        return None
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM items "
            "WHERE LOWER(TRIM(serial)) = LOWER(?) AND deleted_at IS NULL "
            "ORDER BY id LIMIT 1",
            (s,),
        ).fetchone()
    return Item.from_row(row) if row else None


def list_items(
    search: str = "",
    group: str = "",
    type_: str = "",
    brand: str = "",
    status: str = "",
    include_deleted: bool = False,
) -> list[Item]:
    """Return items filtered by text search and dropdown filters."""
    clauses: list[str] = []
    params: list = []

    if not include_deleted:
        clauses.append("deleted_at IS NULL")

    if search:
        like = f"%{search.lower()}%"
        clauses.append(
            "("
            "LOWER(COALESCE(group_name,'')) LIKE ? OR "
            "LOWER(COALESCE(type,''))      LIKE ? OR "
            "LOWER(COALESCE(brand,''))     LIKE ? OR "
            "LOWER(COALESCE(model,''))     LIKE ? OR "
            "LOWER(COALESCE(info,''))      LIKE ? OR "
            "LOWER(COALESCE(serial,''))    LIKE ? OR "
            "LOWER(COALESCE(location,''))  LIKE ?"
            ")"
        )
        params.extend([like] * 7)
    if group:
        clauses.append("group_name = ?")
        params.append(group)
    if type_:
        clauses.append("type = ?")
        params.append(type_)
    if brand:
        clauses.append("brand = ?")
        params.append(brand)
    if status:
        clauses.append("status = ?")
        params.append(status)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM items{where} ORDER BY group_name, type, brand, model"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [Item.from_row(r) for r in rows]


def list_trash() -> list[Item]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE deleted_at IS NOT NULL "
            "ORDER BY deleted_at DESC"
        ).fetchall()
    return [Item.from_row(r) for r in rows]


def distinct_values(column: str) -> list[str]:
    """Return non-empty distinct values for a column, sorted (excludes trash)."""
    allowed = {"group_name", "type", "brand", "status", "store", "location"}
    if column not in allowed:
        raise ValueError(f"Unknown column: {column}")
    with connect() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT {column} AS v FROM items "
            f"WHERE {column} IS NOT NULL AND TRIM({column}) <> '' "
            f"AND deleted_at IS NULL ORDER BY v"
        ).fetchall()
    return [r["v"] for r in rows]


def counts_by(column: str) -> list[tuple[str, int]]:
    allowed = {"group_name", "type", "brand", "status"}
    if column not in allowed:
        raise ValueError(f"Unknown column: {column}")
    with connect() as conn:
        rows = conn.execute(
            f"SELECT {column} AS k, COUNT(*) AS c FROM items "
            f"WHERE {column} IS NOT NULL AND TRIM({column}) <> '' "
            f"AND deleted_at IS NULL "
            f"GROUP BY {column} ORDER BY c DESC"
        ).fetchall()
    return [(r["k"], r["c"]) for r in rows]


def warranty_expiring(within_days: int = config.WARRANTY_SOON_DAYS) -> list[Item]:
    today = date.today()
    horizon = today + timedelta(days=within_days)
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM items
            WHERE deleted_at IS NULL
              AND warranty_end IS NOT NULL AND TRIM(warranty_end) <> ''
              AND warranty_end >= ? AND warranty_end <= ?
            ORDER BY warranty_end
            """,
            (today.isoformat(), horizon.isoformat()),
        ).fetchall()
    return [Item.from_row(r) for r in rows]


def warranty_expired() -> list[Item]:
    today = date.today().isoformat()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE deleted_at IS NULL "
            "AND warranty_end IS NOT NULL AND TRIM(warranty_end) <> '' "
            "AND warranty_end < ? ORDER BY warranty_end",
            (today,),
        ).fetchall()
    return [Item.from_row(r) for r in rows]


def total_quantity() -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity),0) AS s FROM items WHERE deleted_at IS NULL"
        ).fetchone()
    return int(row["s"])


def total_value() -> float:
    """Sum of quantity * unit_price across all non-deleted items."""
    with connect() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity * COALESCE(unit_price,0)),0) AS s "
            "FROM items WHERE deleted_at IS NULL"
        ).fetchone()
    return float(row["s"])


def value_by_group() -> list[tuple[str, float]]:
    """Total value per group, sorted by value descending."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT COALESCE(NULLIF(TRIM(group_name),''), '(none)') AS g, "
            "COALESCE(SUM(quantity * COALESCE(unit_price,0)),0) AS v "
            "FROM items WHERE deleted_at IS NULL "
            "GROUP BY g ORDER BY v DESC"
        ).fetchall()
    return [(r["g"], float(r["v"])) for r in rows]


def qty_by_group() -> list[tuple[str, int]]:
    """Total quantity per group, sorted by quantity descending."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT COALESCE(NULLIF(TRIM(group_name),''), '(none)') AS g, "
            "COALESCE(SUM(quantity),0) AS q "
            "FROM items WHERE deleted_at IS NULL "
            "GROUP BY g ORDER BY q DESC"
        ).fetchall()
    return [(r["g"], int(r["q"])) for r in rows]


def estimate_depreciation(item: Item) -> float:
    """Estimate the current (depreciated) value of an item.

    Uses straight-line depreciation: value drops to zero over
    `depreciation_years` from the purchase date. If no purchase date or
    depreciation period is set, returns the original unit_price.
    """
    if item.depreciation_years <= 0 or not item.purchase_date:
        return item.unit_price
    try:
        purchased = date.fromisoformat(item.purchase_date[:10])
    except ValueError:
        return item.unit_price
    age_days = (date.today() - purchased).days
    age_years = max(0.0, age_days / 365.25)
    if age_years >= item.depreciation_years:
        return 0.0
    remaining = 1.0 - (age_years / item.depreciation_years)
    return max(0.0, item.unit_price * remaining)


def total_depreciated_value() -> float:
    """Sum of depreciated values across all non-deleted items."""
    return sum(estimate_depreciation(it) for it in all_items())


def all_items() -> list[Item]:
    return list_items()


def bulk_insert(items: Iterable[Item]) -> int:
    """Insert many items; returns count inserted. Sets id on each item."""
    count = 0
    with connect() as conn:
        for it in items:
            if it.id is not None:
                cur = conn.execute(
                    """
                    INSERT INTO items
                      (id, group_name, type, brand, model, info, serial, store,
                       purchase_date, status, quantity, location, warranty_end,
                       image_path, unit_price, depreciation_years,
                       created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        it.id,
                        it.group_name, it.type, it.brand, it.model, it.info,
                        it.serial, it.store, it.purchase_date, it.status,
                        it.quantity, it.location, it.warranty_end,
                        it.image_path, it.unit_price, it.depreciation_years,
                        it.created_at or None,
                        it.updated_at or None,
                    ),
                )
            else:
                cur = conn.execute(
                    """
                    INSERT INTO items
                      (group_name, type, brand, model, info, serial, store,
                       purchase_date, status, quantity, location, warranty_end,
                       image_path, unit_price, depreciation_years)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        it.group_name, it.type, it.brand, it.model, it.info,
                        it.serial, it.store, it.purchase_date, it.status,
                        it.quantity, it.location, it.warranty_end,
                        it.image_path, it.unit_price, it.depreciation_years,
                    ),
                )
            if it.id is None:
                it.id = int(cur.lastrowid)
            count += 1
        conn.commit()
    return count


# ---------------------------------------------------------------- multi-image

def add_image(item_id: int, path: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO item_images (item_id, path) VALUES (?, ?)",
            (item_id, path),
        )
        conn.commit()
        return int(cur.lastrowid)


def remove_image(image_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM item_images WHERE id=?", (image_id,))
        conn.commit()


def list_images(item_id: int) -> list[tuple[int, str]]:
    """Return (image_id, path) pairs for an item."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, path FROM item_images WHERE item_id=? ORDER BY id",
            (item_id,),
        ).fetchall()
    return [(r["id"], r["path"]) for r in rows]


def set_images(item_id: int, paths: list[str]) -> None:
    """Replace the full set of images for an item."""
    with connect() as conn:
        conn.execute("DELETE FROM item_images WHERE item_id=?", (item_id,))
        for p in paths:
            conn.execute(
                "INSERT INTO item_images (item_id, path) VALUES (?, ?)",
                (item_id, p),
            )
        conn.commit()


def duplicate_item(item_id: int, new_serial: str = "") -> int:
    """Clone an item (without serial by default) and return the new id."""
    src = get_item(item_id)
    if src is None:
        raise ValueError(f"Item {item_id} not found")
    src.id = None
    src.serial = new_serial
    src.created_at = ""
    src.updated_at = ""
    src.deleted_at = ""
    new_id = create_item(src)
    for _img_id, path in list_images(item_id):
        add_image(new_id, path)
    return new_id


# ----------------------------------------------------------------- contacts

@dataclass(slots=True)
class Contact:
    id: int | None = None
    name: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Contact:
        return cls(
            id=row["id"],
            name=row["name"] or "",
            phone=row["phone"] or "",
            email=row["email"] or "",
            notes=row["notes"] or "",
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
        )

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def create_contact(contact: Contact) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO contacts (name, phone, email, notes) VALUES (?, ?, ?, ?)",
            (contact.name, contact.phone, contact.email, contact.notes),
        )
        conn.commit()
        contact.id = int(cur.lastrowid)
        return contact.id


def update_contact(contact: Contact) -> None:
    if contact.id is None:
        raise ValueError("Contact id is required for update")
    with connect() as conn:
        conn.execute(
            "UPDATE contacts SET name=?, phone=?, email=?, notes=?, "
            "updated_at=datetime('now') WHERE id=?",
            (contact.name, contact.phone, contact.email, contact.notes, contact.id),
        )
        conn.commit()


def delete_contact(contact_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
        conn.commit()


def get_contact(contact_id: int) -> Contact | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM contacts WHERE id=?", (contact_id,)
        ).fetchone()
    return Contact.from_row(row) if row else None


def list_contacts(search: str = "") -> list[Contact]:
    with connect() as conn:
        if search:
            like = f"%{search.lower()}%"
            rows = conn.execute(
                "SELECT * FROM contacts "
                "WHERE LOWER(COALESCE(name,'')) LIKE ? "
                "OR LOWER(COALESCE(phone,'')) LIKE ? "
                "OR LOWER(COALESCE(email,'')) LIKE ? "
                "ORDER BY name",
                (like, like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM contacts ORDER BY name"
            ).fetchall()
    return [Contact.from_row(r) for r in rows]


# -------------------------------------------------------------------- loans

@dataclass(slots=True)
class Loan:
    id: int | None = None
    item_id: int | None = None
    contact_id: int | None = None
    borrower: str = ""
    loaned_on: str = ""
    due_on: str = ""
    returned_on: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Loan:
        return cls(
            id=row["id"],
            item_id=row["item_id"],
            contact_id=row["contact_id"],
            borrower=row["borrower"] or "",
            loaned_on=row["loaned_on"] or "",
            due_on=row["due_on"] or "",
            returned_on=row["returned_on"] or "",
            notes=row["notes"] or "",
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
        )

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "item_id": self.item_id,
            "contact_id": self.contact_id,
            "borrower": self.borrower,
            "loaned_on": self.loaned_on,
            "due_on": self.due_on,
            "returned_on": self.returned_on,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @property
    def is_open(self) -> bool:
        return not self.returned_on

    @property
    def is_overdue(self) -> bool:
        if not self.is_open or not self.due_on:
            return False
        return to_iso(self.due_on) < date.today().isoformat()


def open_loan(
    item_id: int,
    borrower: str,
    contact_id: int | None = None,
    due_on: str = "",
    notes: str = "",
) -> int:
    """Open a new loan for an item and mark the item as LOANED.

    Saves the item's previous status so it can be restored on return.
    """
    if not borrower or not borrower.strip():
        raise ValueError("borrower is required")
    today = date.today().isoformat()
    item = get_item(item_id)
    if item is None:
        raise ValueError(f"Item {item_id} not found")
    if active_loan_for_item(item_id) is not None:
        raise ValueError(f"Item {item_id} is already on loan")
    prev_status = item.status
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO loans
                (item_id, contact_id, borrower, loaned_on, due_on, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (item_id, contact_id, borrower, today, due_on or "", notes),
        )
        loan_id = int(cur.lastrowid)
        if prev_status != "LOANED":
            conn.execute(
                "UPDATE items SET status='LOANED', info=COALESCE(info,'') || ? "
                "WHERE id=?",
                (f"\n[Previous status: {prev_status}]", item_id),
            )
        conn.commit()
    return loan_id


def return_loan(loan_id: int, notes: str = "") -> None:
    """Mark a loan as returned and restore the item's previous status."""
    today = date.today().isoformat()
    with connect() as conn:
        loan_row = conn.execute(
            "SELECT * FROM loans WHERE id=?", (loan_id,)
        ).fetchone()
        if loan_row is None:
            raise ValueError(f"Loan {loan_id} not found")
        if loan_row["returned_on"]:
            return
        conn.execute(
            "UPDATE loans SET returned_on=?, notes=COALESCE(notes,'') || ?, "
            "updated_at=datetime('now') WHERE id=?",
            (today, f"\n{returned_note(notes)}" if notes else "", loan_id),
        )
        item = conn.execute(
            "SELECT * FROM items WHERE id=?", (loan_row["item_id"],)
        ).fetchone()
        if item is not None:
            new_status = extract_previous_status(item["info"] or "")
            if not new_status:
                new_status = "AVAILABLE"
            new_info = strip_previous_status(item["info"] or "")
            conn.execute(
                "UPDATE items SET status=?, info=?, updated_at=datetime('now') "
                "WHERE id=?",
                (new_status, new_info, item["id"]),
            )
        conn.commit()


def returned_note(extra: str) -> str:
    return f"[Returned: {date.today().isoformat()}] {extra}".strip()


def extract_previous_status(info: str) -> str:
    """Pull the previous status marker out of an item's info field."""
    m = re.search(r"\[Previous status:\s*([^\]]+)\]", info)
    return m.group(1).strip() if m else ""


def strip_previous_status(info: str) -> str:
    """Remove the previous-status marker line from an item's info field."""
    cleaned = re.sub(r"\n?\[Previous status:\s*[^\]]+\]", "", info)
    return cleaned.strip()


def get_loan(loan_id: int) -> Loan | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM loans WHERE id=?", (loan_id,)).fetchone()
    return Loan.from_row(row) if row else None


def list_loans(
    open_only: bool = False,
    overdue_only: bool = False,
    item_id: int | None = None,
) -> list[Loan]:
    clauses: list[str] = []
    params: list = []
    if open_only:
        clauses.append("returned_on IS NULL")
    if overdue_only:
        clauses.append("returned_on IS NULL")
        clauses.append("due_on <> ''")
        clauses.append("due_on < ?")
        params.append(date.today().isoformat())
    if item_id is not None:
        clauses.append("item_id = ?")
        params.append(item_id)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM loans{where} ORDER BY loaned_on DESC, id DESC"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [Loan.from_row(r) for r in rows]


def list_item_loans(item_id: int) -> list[Loan]:
    return list_loans(item_id=item_id)


def active_loan_for_item(item_id: int) -> Loan | None:
    """Return the open loan for an item, if any."""
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM loans WHERE item_id=? AND returned_on IS NULL "
            "ORDER BY id DESC LIMIT 1",
            (item_id,),
        ).fetchone()
    return Loan.from_row(row) if row else None


def overdue_loan_item_ids() -> set[int]:
    """Return the set of item_ids with at least one overdue open loan."""
    today = date.today().isoformat()
    with connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT item_id FROM loans "
            "WHERE returned_on IS NULL AND due_on <> '' AND due_on < ?",
            (today,),
        ).fetchall()
    return {r["item_id"] for r in rows}


def on_loan_item_ids() -> set[int]:
    """Return the set of item_ids with at least one open loan."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT item_id FROM loans WHERE returned_on IS NULL"
        ).fetchall()
    return {r["item_id"] for r in rows}


def delete_loan(loan_id: int) -> None:
    with connect() as conn:
        loan_row = conn.execute(
            "SELECT * FROM loans WHERE id=?", (loan_id,)
        ).fetchone()
        if loan_row is None:
            return
        if not loan_row["returned_on"]:
            item = conn.execute(
                "SELECT * FROM items WHERE id=?", (loan_row["item_id"],)
            ).fetchone()
            if item is not None:
                new_status = extract_previous_status(item["info"] or "")
                if not new_status:
                    new_status = "AVAILABLE"
                new_info = strip_previous_status(item["info"] or "")
                conn.execute(
                    "UPDATE items SET status=?, info=?, updated_at=datetime('now') "
                    "WHERE id=?",
                    (new_status, new_info, item["id"]),
                )
        conn.execute("DELETE FROM loans WHERE id=?", (loan_id,))
        conn.commit()
