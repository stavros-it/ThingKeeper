"""Tests for thingkeeper.integrity: checks and cleanup."""

from __future__ import annotations

from thingkeeper import config, integrity
from thingkeeper.repository import create_item


def test_clean_db_passes(repo):
    report = integrity.check_integrity()
    assert report.ok
    assert report.total() == 0


def test_orphan_attachment_detected(repo, sample_item):
    fake = config.ATTACHMENTS_DIR / "orphan.png"
    fake.write_bytes(b"fake")
    report = integrity.check_integrity()
    assert not report.ok
    assert any(p.endswith("orphan.png") for p in report.orphan_attachments)


def test_cleanup_orphan_attachments(repo, sample_item):
    fake = config.ATTACHMENTS_DIR / "orphan1.png"
    fake.write_bytes(b"fake")
    fake2 = config.ATTACHMENTS_DIR / "orphan2.png"
    fake2.write_bytes(b"fake")
    removed = integrity.cleanup_orphan_attachments()
    assert removed >= 2
    report = integrity.check_integrity()
    assert len(report.orphan_attachments) == 0


def test_missing_thumbnail_detected(repo, sample_item):
    it = sample_item(serial="MISSING-THUMB")
    it.image_path = str(config.ATTACHMENTS_DIR / "does_not_exist.png")
    iid = create_item(it)
    report = integrity.check_integrity()
    assert len(report.missing_item_images) == 1
    assert report.missing_item_images[0][0] == iid


def test_clear_missing_item_thumbnails(repo, sample_item):
    it = sample_item(serial="MISSING-THUMB-2")
    it.image_path = str(config.ATTACHMENTS_DIR / "missing.png")
    create_item(it)
    cleared = integrity.clear_missing_item_thumbnails()
    assert cleared >= 1
    report = integrity.check_integrity()
    assert len(report.missing_item_images) == 0


def test_missing_extra_image_row_detected(repo, sample_item):
    from thingkeeper.repository import add_image
    iid = create_item(sample_item(serial="MISSING-EXTRA"))
    add_image(iid, str(config.ATTACHMENTS_DIR / "missing_extra.png"))
    report = integrity.check_integrity()
    assert len(report.missing_extra_images) >= 1


def test_purge_missing_image_rows(repo, sample_item):
    from thingkeeper.repository import add_image, list_images
    iid = create_item(sample_item(serial="PURGE-EXTRA"))
    add_image(iid, str(config.ATTACHMENTS_DIR / "missing_purge.png"))
    assert len(list_images(iid)) == 1
    purged = integrity.purge_missing_image_rows()
    assert purged >= 1
    assert len(list_images(iid)) == 0


def test_referenced_attachment_not_flagged(repo, sample_item):
    img = config.ATTACHMENTS_DIR / "real.png"
    img.write_bytes(b"real-image")
    it = sample_item(serial="REAL-IMG")
    it.image_path = str(img)
    create_item(it)
    report = integrity.check_integrity()
    assert all("real.png" not in p for p in report.orphan_attachments)


def test_integrity_report_total_sums_all_problems(repo, sample_item):
    fake1 = config.ATTACHMENTS_DIR / "orphan_a.png"
    fake1.write_bytes(b"a")
    fake2 = config.ATTACHMENTS_DIR / "orphan_b.png"
    fake2.write_bytes(b"b")
    it = sample_item(serial="MISS-TOT")
    it.image_path = str(config.ATTACHMENTS_DIR / "missing.png")
    create_item(it)
    report = integrity.check_integrity()
    total = (
        len(report.missing_item_images)
        + len(report.missing_extra_images)
        + len(report.orphan_loans_item)
        + len(report.orphan_loans_contact)
        + len(report.orphan_attachments)
    )
    assert report.total() == total
    assert report.total() >= 3
