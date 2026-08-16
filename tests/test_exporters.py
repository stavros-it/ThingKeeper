"""Tests for thingkeeper.exporters: CSV, Excel, HTML, PDF, archive."""

from __future__ import annotations

import pytest

from thingkeeper.exporters import (
    export_archive,
    export_archive_encrypted,
    export_csv,
    export_excel,
    export_html,
    export_pdf_report,
)
from thingkeeper.repository import create_item, list_items


@pytest.fixture
def populated_db(repo, sample_item):
    """Create a handful of items for export tests."""
    for i in range(5):
        create_item(sample_item(serial=f"EXP-{i:03d}", unit_price=100.0 * (i + 1)))
    return list_items()


def test_export_csv(populated_db, tmp_path):
    path = tmp_path / "out.csv"
    export_csv(path)
    assert path.exists()
    assert path.stat().st_size > 0
    content = path.read_text(encoding="utf-8")
    assert "serial" in content.lower()
    assert "EXP-000" in content
    assert "unit_price" in content.lower()


def test_export_excel(populated_db, tmp_path):
    path = tmp_path / "out.xlsx"
    export_excel(path)
    assert path.exists()
    assert path.stat().st_size > 0
    import openpyxl
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    assert ws.max_row >= 6  # header + 5 items


def test_export_html(populated_db, tmp_path):
    path = tmp_path / "out.html"
    export_html(path)
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "<table" in content.lower()
    assert "EXP-000" in content


def test_export_pdf_report(populated_db, tmp_path):
    path = tmp_path / "report.pdf"
    export_pdf_report(path)
    assert path.exists()
    assert path.stat().st_size > 0
    header = path.read_bytes()[:5]
    assert header == b"%PDF-"


def test_export_archive_includes_attachments(repo, sample_item, tmp_path):
    img = tmp_path / "pic.png"
    img.write_bytes(b"fake-image")
    it = sample_item(serial="ATT-1")
    it.image_path = str(img)
    create_item(it)
    archive = tmp_path / "with_attachments.tkz"
    export_archive(archive)
    assert archive.exists()

    import zipfile
    with zipfile.ZipFile(archive, "r") as zf:
        names = zf.namelist()
    assert "items.json.gz" in names
    assert any(n.startswith("attachments/") for n in names)


def test_export_csv_empty_db(repo, tmp_path):
    path = tmp_path / "empty.csv"
    export_csv(path)
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "serial" in content.lower()  # header only


def test_export_archive_encrypted_magic_header(repo, sample_item, tmp_path):
    create_item(sample_item(serial="ENC-EXP-1"))
    path = tmp_path / "enc.tkz"
    export_archive_encrypted(path, "secret")
    assert path.read_bytes()[:6] == b"TKENC1"


def test_exports_include_new_fields(populated_db, tmp_path):
    csv_path = tmp_path / "out.csv"
    export_csv(csv_path)
    content = csv_path.read_text(encoding="utf-8")
    assert "unit_price" in content.lower()
    assert "depreciation" in content.lower()
