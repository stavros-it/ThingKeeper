"""Undo/redo command pattern for item operations.

Each command captures enough state to redo (execute) and undo itself.
The UndoStack holds a bounded history and emits nothing — the owning
window is responsible for refreshing the view and toggling action state
after each push/undo/redo.
"""

from __future__ import annotations

from collections.abc import Callable

from .repository import (
    Item,
    bulk_update,
    create_item,
    duplicate_item,
    hard_delete,
    restore_item,
    soft_delete,
    update_item,
)


class Command:
    """Base class. Subclasses implement redo() and undo()."""

    label: str = "action"

    def redo(self) -> None:
        raise NotImplementedError

    def undo(self) -> None:
        raise NotImplementedError


class CreateItemCommand(Command):
    label = "Create item"

    def __init__(self, item: Item) -> None:
        self._item = item
        self._new_id: int | None = None

    def redo(self) -> None:
        self._new_id = create_item(self._item)

    def undo(self) -> None:
        if self._new_id is not None:
            hard_delete(self._new_id)
            self._item.id = None


class UpdateItemCommand(Command):
    label = "Edit item"

    def __init__(self, old_item: Item, new_item: Item) -> None:
        self._old = old_item
        self._new = new_item

    def redo(self) -> None:
        update_item(self._new)

    def undo(self) -> None:
        update_item(self._old)


class DeleteItemCommand(Command):
    label = "Delete item"

    def __init__(self, item_ids: list[int]) -> None:
        self._ids = item_ids

    def redo(self) -> None:
        for iid in self._ids:
            soft_delete(iid)

    def undo(self) -> None:
        for iid in self._ids:
            restore_item(iid)


class BulkUpdateCommand(Command):
    label = "Bulk edit"

    def __init__(
        self,
        item_ids: list[int],
        old_values: list[dict],
        new_fields: dict,
    ) -> None:
        self._ids = item_ids
        self._old = old_values
        self._new = new_fields

    def redo(self) -> None:
        bulk_update(self._ids, self._new)

    def undo(self) -> None:
        for iid, old in zip(self._ids, self._old):
            bulk_update([iid], old)


class DuplicateItemCommand(Command):
    label = "Duplicate item"

    def __init__(self, source_id: int, new_serial: str = "") -> None:
        self._source_id = source_id
        self._new_serial = new_serial
        self._new_id: int | None = None

    def redo(self) -> None:
        self._new_id = duplicate_item(self._source_id, self._new_serial)

    def undo(self) -> None:
        if self._new_id is not None:
            hard_delete(self._new_id)


class UndoStack:
    """Bounded undo/redo stack."""

    def __init__(self, limit: int = 100) -> None:
        self._undo: list[Command] = []
        self._redo: list[Command] = []
        self._limit = limit
        self._changed: Callable[[], None] | None = None

    def set_changed_callback(self, cb: Callable[[], None]) -> None:
        self._changed = cb

    def push(self, cmd: Command) -> None:
        cmd.redo()
        self._undo.append(cmd)
        self._redo.clear()
        if len(self._undo) > self._limit:
            self._undo.pop(0)
        if self._changed:
            self._changed()

    def undo(self) -> None:
        if not self._undo:
            return
        cmd = self._undo.pop()
        cmd.undo()
        self._redo.append(cmd)
        if self._changed:
            self._changed()

    def redo(self) -> None:
        if not self._redo:
            return
        cmd = self._redo.pop()
        cmd.redo()
        self._undo.append(cmd)
        if self._changed:
            self._changed()

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        if self._changed:
            self._changed()

    def undo_label(self) -> str:
        return self._undo[-1].label if self._undo else ""

    def redo_label(self) -> str:
        return self._redo[-1].label if self._redo else ""
