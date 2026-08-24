"""Tests for thingkeeper.importers: Excel, CSV, archive, encrypted archive."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from thingkeeper.exporters import (
    export_archive,
    export_archive_encrypted,
    is_encrypted_archive,
)
from thingkeeper.importers import (
    import_archive,
    import_archive_encrypted,
    import_csv,
    import_excel,
)
from thingkeeper.repository import (
    add_image,
    create_item,
    hard_delete,
    list_images,
    list_items,
    list_receipts,
)


def _write_csv(path: Path, rows: list[list[str]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


def test_import_csv_basic(repo, tmp_path):
    csv_path = tmp_path / "items.csv"
    _write_csv(csv_path, [
        ["Group", "Type", "Brand", "Model", "Serial", "Status", "Quantity"],
        ["IT", "laptop", "Dell", "XPS 13", "CSV-001", "AVAILABLE", "1"],
        ["IT", "laptop", "HP", "EliteBook", "CSV-002", "IN USE", "2"],
    ])
    result = import_csv(csv_path)
    assert result.imported == 2
    assert result.skipped == 0
    assert len(list_items()) == 2


def test_import_csv_aliases(repo, tmp_path):
    csv_path = tmp_path / "items.csv"
    _write_csv(csv_path, [
        ["group", "type", "brand", "model", "serial", "qty", "price"],
        ["AV", "tv", "Sony", "Bravia", "CSV-003", "1", "800"],
    ])
    result = import_csv(csv_path)
    assert result.imported == 1
    items = list_items()
    assert items[0].unit_price == 800.0


def test_import_csv_empty(tmp_path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("")
    result = import_csv(csv_path)
    assert result.imported == 0
    assert len(result.errors) >= 1


def test_import_csv_no_recognised_columns(repo, tmp_path):
    csv_path = tmp_path / "bad.csv"
    _write_csv(csv_path, [
        ["foo", "bar", "baz"],
        ["1", "2", "3"],
    ])
    result = import_csv(csv_path)
    assert result.imported == 0
    assert any("recognised" in e.lower() for e in result.errors)


def test_import_csv_skips_blank_rows(repo, tmp_path):
    csv_path = tmp_path / "items.csv"
    _write_csv(csv_path, [
        ["Group", "Type", "Brand", "Model", "Serial"],
        ["IT", "laptop", "Dell", "XPS", "S1"],
        ["", "", "", "", ""],
        ["IT", "laptop", "HP", "Elite", "S2"],
    ])
    result = import_csv(csv_path)
    assert result.imported == 2
    assert result.skipped == 1


def test_import_excel_real_file(repo, excel_path):
    result = import_excel(excel_path)
    assert result.imported == 5
    assert len(list_items()) == 5


def test_import_excel_fields_parsed(repo, excel_path):
    import_excel(excel_path)
    items = list_items()
    assert len(items) == 5
    # The group/type columns should be populated for all items.
    assert all(it.group_name for it in items)
    assert all(it.type for it in items)
    # unit_price and depreciation should have been parsed.
    priced = [it for it in items if it.unit_price and it.unit_price > 0]
    assert len(priced) == 5


# ----------------------------------------------------------- archives
def test_archive_round_trip(repo, sample_item, tmp_path):
    for i in range(5):
        create_item(sample_item(serial=f"ARC-{i:03d}"))
    archive_path = tmp_path / "test_archive.tkz"
    export_archive(archive_path)
    assert archive_path.exists()
    assert archive_path.stat().st_size > 0

    # Wipe DB and re-import
    for it in list_items():
        hard_delete(it.id)
    assert len(list_items()) == 0

    result = import_archive(archive_path)
    assert result.imported == 5


def test_encrypted_archive_round_trip(repo, sample_item, tmp_path):
    for i in range(3):
        create_item(sample_item(serial=f"ENC-{i:03d}"))
    path = tmp_path / "enc.tkz"
    passphrase = "correct horse battery staple"
    export_archive_encrypted(path, passphrase)
    assert is_encrypted_archive(path)

    for it in list_items():
        hard_delete(it.id)
    assert len(list_items()) == 0

    result = import_archive_encrypted(path, passphrase)
    assert result.imported == 3


def test_encrypted_archive_wrong_passphrase(repo, sample_item, tmp_path):
    create_item(sample_item(serial="ENC-W-1"))
    path = tmp_path / "enc_wrong.tkz"
    export_archive_encrypted(path, "right-passphrase")
    result = import_archive_encrypted(path, "wrong-passphrase")
    assert result.imported == 0
    assert any("passphrase" in e.lower() for e in result.errors)


def test_encrypted_archive_empty_passphrase_rejected(repo, tmp_path):
    path = tmp_path / "enc_empty.tkz"
    with pytest.raises(ValueError):
        export_archive_encrypted(path, "")


def test_is_encrypted_archive_detects_plain(repo, sample_item, tmp_path):
    create_item(sample_item(serial="PLAIN-1"))
    path = tmp_path / "plain.tkz"
    export_archive(path)
    assert not is_encrypted_archive(path)


def test_import_archive_missing_file(repo, tmp_path):
    with pytest.raises(FileNotFoundError):
        import_archive(tmp_path / "does_not_exist.tkz")


def test_archive_round_trip_preserves_receipts(repo, sample_item, tmp_path):
    """Receipts (kind='receipt') and images must survive a .tkz export/import."""
    iid = create_item(sample_item(serial="RCP-ARC-1"))
    img_path = tmp_path / "sample.png"
    img_path.write_bytes(b"\x89PNG\r\n\x1a\n fake png")
    rcp_path = tmp_path / "invoice.pdf"
    rcp_path.write_bytes(b"%PDF-1.4 fake invoice")
    add_image(iid, str(img_path), kind="image")
    add_image(iid, str(rcp_path), kind="receipt")
    assert len(list_images(iid)) == 1
    assert len(list_receipts(iid)) == 1

    archive_path = tmp_path / "receipts.tkz"
    export_archive(archive_path)

    for it in list_items():
        hard_delete(it.id)
    assert len(list_items()) == 0

    result = import_archive(archive_path)
    assert result.imported == 1
    restored = list_items()[0]
    assert len(list_images(restored.id)) == 1
    assert len(list_receipts(restored.id)) == 1
