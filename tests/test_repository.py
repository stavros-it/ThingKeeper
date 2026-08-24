"""Tests for thingkeeper.repository: CRUD, aggregations, loans, contacts."""

from __future__ import annotations

from datetime import date

import pytest

from thingkeeper.repository import (
    Contact,
    active_loan_for_item,
    add_image,
    bulk_insert,
    bulk_update,
    counts_by,
    create_contact,
    create_item,
    delete_contact,
    delete_loan,
    distinct_values,
    duplicate_item,
    estimate_depreciation,
    find_by_serial,
    get_item,
    hard_delete,
    list_contacts,
    list_images,
    list_item_loans,
    list_items,
    list_loans,
    list_receipts,
    on_loan_item_ids,
    open_loan,
    overdue_loan_item_ids,
    qty_by_group,
    remove_image,
    restore_item,
    return_loan,
    set_images,
    set_receipts,
    soft_delete,
    total_depreciated_value,
    total_quantity,
    total_value,
    update_item,
    value_by_group,
)


def test_create_and_get_item(repo, sample_item):
    it = sample_item()
    iid = create_item(it)
    assert iid > 0
    got = get_item(iid)
    assert got is not None
    assert got.serial == "TEST-001"
    assert got.unit_price == 1500.0
    assert got.depreciation_years == 5.0


def test_update_item(repo, sample_item):
    it = sample_item()
    iid = create_item(it)
    it.id = iid
    it.brand = "HP"
    it.unit_price = 2000.0
    update_item(it)
    got = get_item(iid)
    assert got.brand == "HP"
    assert got.unit_price == 2000.0


def test_soft_delete_and_restore(repo, sample_item):
    it = sample_item()
    iid = create_item(it)
    soft_delete(iid)
    # Soft-deleted items don't appear in list_items (they're in trash)
    assert len(list_items()) == 0
    restore_item(iid)
    assert len(list_items()) == 1


def test_hard_delete(repo, sample_item):
    it = sample_item()
    iid = create_item(it)
    hard_delete(iid)
    assert get_item(iid) is None


def test_list_items_with_search(repo, sample_item):
    for i in range(5):
        create_item(sample_item(serial=f"S-{i:03d}", brand="Dell"))
    for i in range(3):
        create_item(sample_item(serial=f"H-{i:03d}", brand="HP"))
    dell = list_items(search="Dell")
    assert len(dell) == 5
    hp = list_items(search="HP")
    assert len(hp) == 3


def test_list_items_status_filter(repo, sample_item):
    create_item(sample_item(serial="A", status="AVAILABLE"))
    create_item(sample_item(serial="B", status="BROKEN"))
    avail = list_items(status="AVAILABLE")
    assert len(avail) == 1
    assert avail[0].serial == "A"


def test_distinct_values(repo, sample_item):
    create_item(sample_item(serial="1", group_name="IT"))
    create_item(sample_item(serial="2", group_name="IT"))
    create_item(sample_item(serial="3", group_name="AV"))
    groups = distinct_values("group_name")
    assert set(groups) == {"IT", "AV"}


def test_counts_by(repo, sample_item):
    create_item(sample_item(serial="1", group_name="IT"))
    create_item(sample_item(serial="2", group_name="IT"))
    create_item(sample_item(serial="3", group_name="AV"))
    counts = dict(counts_by("group_name"))
    assert counts["IT"] == 2
    assert counts["AV"] == 1


def test_total_quantity(repo, sample_item):
    create_item(sample_item(serial="1", quantity=3))
    create_item(sample_item(serial="2", quantity=2))
    assert total_quantity() == 5


def test_total_value(repo, sample_item):
    create_item(sample_item(serial="1", unit_price=100.0, quantity=2))
    create_item(sample_item(serial="2", unit_price=50.0, quantity=4))
    assert total_value() == pytest.approx(400.0)


def test_value_by_group(repo, sample_item):
    create_item(sample_item(serial="1", group_name="IT", unit_price=100.0, quantity=2))
    create_item(sample_item(serial="2", group_name="AV", unit_price=50.0, quantity=4))
    vg = dict(value_by_group())
    assert vg["IT"] == pytest.approx(200.0)
    assert vg["AV"] == pytest.approx(200.0)


def test_qty_by_group(repo, sample_item):
    create_item(sample_item(serial="1", group_name="IT", quantity=3))
    create_item(sample_item(serial="2", group_name="AV", quantity=4))
    qg = dict(qty_by_group())
    assert qg["IT"] == 3
    assert qg["AV"] == 4


def test_estimate_depreciation_recent_purchase(repo, sample_item):
    today = date.today().isoformat()
    it = sample_item(serial="DEP-1", purchase_date=today, unit_price=1000.0,
                    depreciation_years=5.0)
    create_item(it)
    items = list_items(search="DEP-1")
    dep = estimate_depreciation(items[0])
    assert dep == pytest.approx(1000.0, rel=0.01)


def test_estimate_depreciation_fully_depreciated(repo, sample_item):
    it = sample_item(
        serial="DEP-2",
        purchase_date="2010-01-01",
        unit_price=1000.0,
        depreciation_years=5.0,
    )
    create_item(it)
    items = list_items(search="DEP-2")
    dep = estimate_depreciation(items[0])
    assert dep == pytest.approx(0.0, abs=0.01)


def test_estimate_depreciation_no_price(repo, sample_item):
    it = sample_item(serial="DEP-3", unit_price=0.0, depreciation_years=5.0)
    create_item(it)
    items = list_items(search="DEP-3")
    dep = estimate_depreciation(items[0])
    assert dep == 0.0


def test_total_depreciated_value(repo, sample_item):
    today = date.today().isoformat()
    create_item(sample_item(serial="V1", purchase_date=today,
                            unit_price=500.0, depreciation_years=5.0))
    assert total_depreciated_value() >= 0.0


def test_bulk_insert(repo, sample_item):
    items = [sample_item(serial=f"B-{i:03d}") for i in range(10)]
    n = bulk_insert(items)
    assert n == 10


def test_bulk_update(repo, sample_item):
    ids = [create_item(sample_item(serial=f"U-{i:03d}")) for i in range(3)]
    bulk_update(ids, {"status": "BROKEN"})
    for iid in ids:
        assert get_item(iid).status == "BROKEN"


def test_duplicate_item(repo, sample_item):
    iid = create_item(sample_item(serial="DUP-001"))
    new_id = duplicate_item(iid, new_serial="DUP-002")
    assert new_id != iid
    assert get_item(new_id).serial == "DUP-002"


def test_find_by_serial(repo, sample_item):
    create_item(sample_item(serial="FIND-ME"))
    it = find_by_serial("FIND-ME")
    assert it is not None
    assert it.serial == "FIND-ME"
    assert find_by_serial("DOES-NOT-EXIST") is None


# ----------------------------------------------------------- images
def test_add_and_list_images(repo, sample_item, tmp_path):
    iid = create_item(sample_item(serial="IMG-1"))
    fake = tmp_path / "photo.png"
    fake.write_bytes(b"fake")
    img_id = add_image(iid, str(fake))
    images = list_images(iid)
    assert len(images) == 1
    assert images[0][0] == img_id


def test_set_images_replaces(repo, sample_item, tmp_path):
    iid = create_item(sample_item(serial="IMG-2"))
    f1 = tmp_path / "a.png"
    f1.write_bytes(b"a")
    f2 = tmp_path / "b.png"
    f2.write_bytes(b"b")
    set_images(iid, [str(f1)])
    assert len(list_images(iid)) == 1
    set_images(iid, [str(f1), str(f2)])
    assert len(list_images(iid)) == 2


def test_remove_image(repo, sample_item, tmp_path):
    iid = create_item(sample_item(serial="IMG-3"))
    f = tmp_path / "x.png"
    f.write_bytes(b"x")
    img_id = add_image(iid, str(f))
    remove_image(img_id)
    assert len(list_images(iid)) == 0


# ----------------------------------------------------------- receipts
def test_add_and_list_receipts(repo, sample_item, tmp_path):
    iid = create_item(sample_item(serial="RCP-1"))
    f = tmp_path / "invoice.pdf"
    f.write_bytes(b"%PDF-1.4 fake")
    add_image(iid, str(f), kind="receipt")
    receipts = list_receipts(iid)
    assert len(receipts) == 1
    assert receipts[0][1] == str(f)


def test_set_receipts_replaces_only_receipts(repo, sample_item, tmp_path):
    iid = create_item(sample_item(serial="RCP-2"))
    img = tmp_path / "photo.png"
    img.write_bytes(b"img")
    add_image(iid, str(img), kind="image")
    r1 = tmp_path / "r1.pdf"
    r1.write_bytes(b"r1")
    r2 = tmp_path / "r2.pdf"
    r2.write_bytes(b"r2")
    set_receipts(iid, [str(r1)])
    assert len(list_receipts(iid)) == 1
    assert len(list_images(iid)) == 1  # image preserved
    set_receipts(iid, [str(r1), str(r2)])
    assert len(list_receipts(iid)) == 2
    assert len(list_images(iid)) == 1  # image still preserved


def test_set_images_preserves_receipts(repo, sample_item, tmp_path):
    iid = create_item(sample_item(serial="RCP-3"))
    r = tmp_path / "receipt.pdf"
    r.write_bytes(b"r")
    set_receipts(iid, [str(r)])
    img = tmp_path / "image.png"
    img.write_bytes(b"i")
    set_images(iid, [str(img)])
    assert len(list_images(iid)) == 1
    assert len(list_receipts(iid)) == 1  # receipt survived set_images


def test_duplicate_item_copies_receipts(repo, sample_item, tmp_path):
    iid = create_item(sample_item(serial="RCP-4"))
    img = tmp_path / "image.png"
    img.write_bytes(b"i")
    r = tmp_path / "invoice.pdf"
    r.write_bytes(b"r")
    add_image(iid, str(img), kind="image")
    add_image(iid, str(r), kind="receipt")
    new_id = duplicate_item(iid, new_serial="RCP-4-DUP")
    assert len(list_images(new_id)) == 1
    assert len(list_receipts(new_id)) == 1


# ----------------------------------------------------------- contacts
def test_create_and_list_contacts(repo):
    cid = create_contact(Contact(name="Alice", phone="555-1000",
                                 email="alice@example.com"))
    assert cid > 0
    contacts = list_contacts()
    assert len(contacts) == 1
    assert contacts[0].name == "Alice"


def test_search_contacts(repo):
    create_contact(Contact(name="Alice"))
    create_contact(Contact(name="Bob"))
    create_contact(Contact(name="Charlie"))
    res = list_contacts(search="ali")
    assert len(res) == 1
    assert res[0].name == "Alice"


def test_delete_contact(repo):
    cid = create_contact(Contact(name="Alice"))
    delete_contact(cid)
    assert len(list_contacts()) == 0


# ----------------------------------------------------------- loans
def test_open_and_return_loan(repo, sample_item):
    iid = create_item(sample_item(serial="LOAN-1"))
    today = date.today().isoformat()
    loan_id = open_loan(iid, borrower="Alice", due_on=today, notes="test")
    assert loan_id > 0
    loan = active_loan_for_item(iid)
    assert loan is not None
    assert loan.borrower == "Alice"
    return_loan(loan_id)
    assert active_loan_for_item(iid) is None


def test_on_loan_item_ids(repo, sample_item):
    i1 = create_item(sample_item(serial="L1"))
    i2 = create_item(sample_item(serial="L2"))
    today = date.today().isoformat()
    open_loan(i1, borrower="Alice", due_on=today)
    on_loan = on_loan_item_ids()
    assert i1 in on_loan
    assert i2 not in on_loan


def test_overdue_loan_item_ids(repo, sample_item):
    iid = create_item(sample_item(serial="OVERDUE-1"))
    open_loan(iid, borrower="Bob", due_on="2020-01-01")
    overdue = overdue_loan_item_ids()
    assert iid in overdue


def test_list_item_loans(repo, sample_item):
    iid = create_item(sample_item(serial="LH-1"))
    today = date.today().isoformat()
    open_loan(iid, borrower="Alice", due_on=today)
    loans = list_item_loans(iid)
    assert len(loans) == 1


def test_list_loans_filter(repo, sample_item):
    i1 = create_item(sample_item(serial="LF-1"))
    i2 = create_item(sample_item(serial="LF-2"))
    today = date.today().isoformat()
    open_loan(i1, borrower="Alice", due_on=today)
    open_loan(i2, borrower="Bob", due_on="2020-01-01")
    assert len(list_loans(open_only=True)) == 2
    assert len(list_loans(overdue_only=True)) == 1


def test_delete_loan(repo, sample_item):
    iid = create_item(sample_item(serial="DL-1"))
    today = date.today().isoformat()
    loan_id = open_loan(iid, borrower="Alice", due_on=today)
    delete_loan(loan_id)
    assert active_loan_for_item(iid) is None
