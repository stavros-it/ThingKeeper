"""Data access layer: CRUD, filtering and aggregation for items."""

from __future__ import annotations

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
    created_at: str = ""
    updated_at: str = ""

    # Convenience: column order used by importers/exporters.
    COLUMNS: tuple = field(default_factory=lambda: (
        "group_name", "type", "brand", "model", "info", "serial",
        "store", "purchase_date", "status", "quantity", "location",
        "warranty_end", "image_path",
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
        }


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
    # Common European formats.
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return s  # fall back to whatever was given


def create_item(item: Item) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO items
                (group_name, type, brand, model, info, serial, store,
                 purchase_date, status, quantity, location, warranty_end, image_path)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                item.group_name, item.type, item.brand, item.model, item.info,
                item.serial, item.store, item.purchase_date, item.status,
                item.quantity, item.location, item.warranty_end, item.image_path,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def update_item(item: Item) -> None:
    if item.id is None:
        raise ValueError("Item id is required for update")
    with connect() as conn:
        conn.execute(
            """
            UPDATE items SET
                group_name=?, type=?, brand=?, model=?, info=?, serial=?, store=?,
                purchase_date=?, status=?, quantity=?, location=?, warranty_end=?,
                image_path=?, updated_at=datetime('now')
            WHERE id=?
            """,
            (
                item.group_name, item.type, item.brand, item.model, item.info,
                item.serial, item.store, item.purchase_date, item.status,
                item.quantity, item.location, item.warranty_end, item.image_path,
                item.id,
            ),
        )
        conn.commit()


def delete_item(item_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit()


def get_item(item_id: int) -> Item | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return Item.from_row(row) if row else None


def find_by_serial(serial: str) -> Item | None:
    """Return the first item whose serial matches (case-insensitive, trimmed)."""
    s = (serial or "").strip()
    if not s:
        return None
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM items WHERE LOWER(TRIM(serial)) = LOWER(?) LIMIT 1",
            (s,),
        ).fetchone()
    return Item.from_row(row) if row else None


def list_items(
    search: str = "",
    group: str = "",
    type_: str = "",
    brand: str = "",
    status: str = "",
) -> list[Item]:
    """Return items filtered by text search and dropdown filters."""
    clauses: list[str] = []
    params: list = []

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


def distinct_values(column: str) -> list[str]:
    """Return non-empty distinct values for a column, sorted."""
    allowed = {"group_name", "type", "brand", "status", "store", "location"}
    if column not in allowed:
        raise ValueError(f"Unknown column: {column}")
    with connect() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT {column} AS v FROM items "
            f"WHERE {column} IS NOT NULL AND TRIM({column}) <> '' ORDER BY v"
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
            f"GROUP BY {column} ORDER BY c DESC"
        ).fetchall()
    return [(r["k"], r["c"]) for r in rows]


def warranty_expiring(within_days: int = config.WARRANTY_SOON_DAYS) -> list[Item]:
    """Items whose warranty_end is in the future but within `within_days`."""
    today = date.today()
    horizon = today + timedelta(days=within_days)
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM items
            WHERE warranty_end IS NOT NULL AND TRIM(warranty_end) <> ''
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
            "SELECT * FROM items WHERE warranty_end < ? ORDER BY warranty_end",
            (today,),
        ).fetchall()
    return [Item.from_row(r) for r in rows]


def total_quantity() -> int:
    with connect() as conn:
        row = conn.execute("SELECT COALESCE(SUM(quantity),0) AS s FROM items").fetchone()
    return int(row["s"])


def all_items() -> list[Item]:
    return list_items()


def bulk_insert(items: Iterable[Item]) -> int:
    """Insert many items; returns count inserted."""
    count = 0
    with connect() as conn:
        for it in items:
            conn.execute(
                """
                INSERT INTO items
                  (group_name, type, brand, model, info, serial, store,
                   purchase_date, status, quantity, location, warranty_end, image_path)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    it.group_name, it.type, it.brand, it.model, it.info,
                    it.serial, it.store, it.purchase_date, it.status,
                    it.quantity, it.location, it.warranty_end, it.image_path,
                ),
            )
            count += 1
        conn.commit()
    return count
