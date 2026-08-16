"""Data integrity checker and attachment cleanup.

`check_integrity()` reports problems:
- items with image_path pointing to a missing file
- item_images rows pointing to missing files
- loans referencing a missing item
- loans referencing a missing contact
- attachments on disk that are not referenced by any item

`cleanup_orphan_attachments()` removes unreferenced files in
data/attachments/ and returns the count removed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .database import connect


@dataclass
class IntegrityReport:
    missing_item_images: list[tuple[int, str]] = field(default_factory=list)
    missing_extra_images: list[tuple[int, int, str]] = field(default_factory=list)
    orphan_loans_item: list[tuple[int, int]] = field(default_factory=list)
    orphan_loans_contact: list[tuple[int, int]] = field(default_factory=list)
    orphan_attachments: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.missing_item_images
            or self.missing_extra_images
            or self.orphan_loans_item
            or self.orphan_loans_contact
            or self.orphan_attachments
        )

    def total(self) -> int:
        return (
            len(self.missing_item_images)
            + len(self.missing_extra_images)
            + len(self.orphan_loans_item)
            + len(self.orphan_loans_contact)
            + len(self.orphan_attachments)
        )


def _referenced_attachment_names() -> set[str]:
    """All attachment basenames referenced by any item, active or trashed."""
    names: set[str] = set()
    conn = connect()
    try:
        for (img,) in conn.execute(
            "SELECT image_path FROM items WHERE image_path IS NOT NULL AND image_path != ''"
        ):
            if img:
                names.add(Path(img).name)
        for img_id, img in list_images_all():
            names.add(Path(img).name)
    finally:
        conn.close()
    return names


def list_images_all() -> list[tuple[int, str]]:
    """Return (image_id, path) for all rows in item_images."""
    conn = connect()
    try:
        return [(int(r[0]), str(r[1])) for r in conn.execute(
            "SELECT id, path FROM item_images ORDER BY id"
        )]
    finally:
        conn.close()


def check_integrity() -> IntegrityReport:
    """Scan the database and attachments folder for integrity problems."""
    report = IntegrityReport()
    conn = connect()
    try:
        for item_id, img in conn.execute(
            "SELECT id, image_path FROM items "
            "WHERE image_path IS NOT NULL AND image_path != ''"
        ):
            if not Path(img).exists():
                report.missing_item_images.append((int(item_id), str(img)))

        for img_id, img_path in list_images_all():
            if not Path(img_path).exists():
                # Look up the owning item_id for the report.
                row = conn.execute(
                    "SELECT item_id FROM item_images WHERE id = ?", (img_id,)
                ).fetchone()
                owner = int(row[0]) if row else 0
                report.missing_extra_images.append((owner, img_id, img_path))

        for loan_id, item_id in conn.execute(
            "SELECT id, item_id FROM loans"
        ):
            row = conn.execute(
                "SELECT 1 FROM items WHERE id = ?", (item_id,)
            ).fetchone()
            if row is None:
                report.orphan_loans_item.append((int(loan_id), int(item_id)))

        for loan_id, contact_id in conn.execute(
            "SELECT id, contact_id FROM loans WHERE contact_id IS NOT NULL"
        ):
            row = conn.execute(
                "SELECT 1 FROM contacts WHERE id = ?", (contact_id,)
            ).fetchone()
            if row is None:
                report.orphan_loans_contact.append((int(loan_id), int(contact_id)))
    finally:
        conn.close()

    referenced = _referenced_attachment_names()
    if config.ATTACHMENTS_DIR.exists():
        for p in config.ATTACHMENTS_DIR.iterdir():
            if p.is_file() and p.name not in referenced:
                report.orphan_attachments.append(str(p))
    return report


def cleanup_orphan_attachments() -> int:
    """Delete attachment files not referenced by any item. Returns count."""
    referenced = _referenced_attachment_names()
    removed = 0
    if not config.ATTACHMENTS_DIR.exists():
        return 0
    for p in config.ATTACHMENTS_DIR.iterdir():
        if p.is_file() and p.name not in referenced:
            try:
                p.unlink()
                removed += 1
            except OSError:
                pass
    return removed


def purge_missing_image_rows() -> int:
    """Remove item_images rows whose file no longer exists. Returns count."""
    removed = 0
    conn = connect()
    try:
        for img_id, img_path in list_images_all():
            if not Path(img_path).exists():
                conn.execute("DELETE FROM item_images WHERE id = ?", (img_id,))
                removed += 1
        conn.commit()
    finally:
        conn.close()
    return removed


def clear_missing_item_thumbnails() -> int:
    """Set image_path=NULL on items whose file no longer exists. Returns count."""
    removed = 0
    conn = connect()
    try:
        for item_id, img in conn.execute(
            "SELECT id, image_path FROM items "
            "WHERE image_path IS NOT NULL AND image_path != ''"
        ):
            if not Path(img).exists():
                conn.execute(
                    "UPDATE items SET image_path = NULL WHERE id = ?", (item_id,)
                )
                removed += 1
        conn.commit()
    finally:
        conn.close()
    return removed
