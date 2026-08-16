"""Serial / barcode scanning helper.

This supports the most common inventory workflow: a USB barcode scanner that
behaves as a keyboard (a "keyboard wedge"). When the user pulls the trigger
the scanner types the code quickly and ends with Enter. We just need a
focused text field ready to receive that input.

No camera-based decoding is required, which keeps dependencies minimal.
"""

from __future__ import annotations

from .repository import Item, find_by_serial


def lookup_serial(serial: str) -> Item | None:
    """Return the item whose serial matches, or None."""
    return find_by_serial(serial)
