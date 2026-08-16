"""Tests for thingkeeper.commands: undo/redo command pattern."""

from __future__ import annotations

from thingkeeper.commands import (
    BulkUpdateCommand,
    CreateItemCommand,
    DeleteItemCommand,
    DuplicateItemCommand,
    UndoStack,
    UpdateItemCommand,
)
from thingkeeper.repository import (
    create_item,
    get_item,
    list_items,
)


def test_undo_stack_initial_state():
    stack = UndoStack()
    assert not stack.can_undo
    assert not stack.can_redo


def test_create_item_command_undo_redo(repo, sample_item):
    stack = UndoStack()
    cmd = CreateItemCommand(sample_item(serial="CMD-1"))
    stack.push(cmd)
    assert len(list_items()) == 1
    assert stack.can_undo
    stack.undo()
    assert len(list_items()) == 0
    assert stack.can_redo
    stack.redo()
    assert len(list_items()) == 1


def test_update_item_command(repo, sample_item):
    stack = UndoStack()
    old = sample_item(serial="CMD-2")
    iid = create_item(old)
    old.id = iid
    new = sample_item(serial="CMD-2")
    new.id = iid
    new.brand = "Updated"
    stack.push(UpdateItemCommand(old, new))
    assert get_item(iid).brand == "Updated"
    stack.undo()
    assert get_item(iid).brand == "Dell"
    stack.redo()
    assert get_item(iid).brand == "Updated"


def test_delete_item_command(repo, sample_item):
    stack = UndoStack()
    iid = create_item(sample_item(serial="CMD-3"))
    stack.push(DeleteItemCommand([iid]))
    # soft-deleted items don't appear in list_items
    assert len(list_items()) == 0
    stack.undo()
    assert len(list_items()) == 1


def test_bulk_update_command(repo, sample_item):
    stack = UndoStack()
    items = [sample_item(serial=f"BULK-{i}") for i in range(3)]
    ids = [create_item(it) for it in items]
    old_values = [{"status": "AVAILABLE"} for _ in ids]
    stack.push(BulkUpdateCommand(ids, old_values, {"status": "BROKEN"}))
    for iid in ids:
        assert get_item(iid).status == "BROKEN"
    stack.undo()
    for iid in ids:
        assert get_item(iid).status == "AVAILABLE"


def test_duplicate_item_command(repo, sample_item):
    stack = UndoStack()
    iid = create_item(sample_item(serial="DUP-CMD-1"))
    stack.push(DuplicateItemCommand(iid, "DUP-CMD-2"))
    items = list_items()
    assert len(items) == 2
    stack.undo()
    assert len(list_items()) == 1
    stack.redo()
    assert len(list_items()) == 2


def test_undo_stack_clear(repo, sample_item):
    stack = UndoStack()
    stack.push(CreateItemCommand(sample_item(serial="CLR-1")))
    assert stack.can_undo
    stack.clear()
    assert not stack.can_undo
    assert not stack.can_redo


def test_undo_stack_callback(repo, sample_item):
    calls = []
    stack = UndoStack()
    stack.set_changed_callback(lambda: calls.append(True))
    stack.push(CreateItemCommand(sample_item(serial="CB-1")))
    stack.undo()
    stack.redo()
    assert len(calls) >= 3
