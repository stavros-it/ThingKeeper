"""Tests for thingkeeper.ui.date_fmt."""

from __future__ import annotations

from thingkeeper.ui import date_fmt


def test_qt_date_format_returns_nonempty_string() -> None:
    fmt = date_fmt.qt_date_format()
    assert isinstance(fmt, str)
    assert fmt


def test_format_iso_date_empty_input_returned_unchanged() -> None:
    assert date_fmt.format_iso_date("") == ""
    assert date_fmt.format_iso_date("   ") == "   "


def test_format_iso_date_malformed_input_returned_unchanged() -> None:
    bad = "not-a-date"
    assert date_fmt.format_iso_date(bad) == bad


def test_format_iso_date_short_input_returned_unchanged() -> None:
    assert date_fmt.format_iso_date("2024") == "2024"


def test_format_iso_date_valid_iso_returns_nonempty() -> None:
    out = date_fmt.format_iso_date("2024-03-09")
    assert isinstance(out, str)
    assert out


def test_format_iso_date_does_not_return_iso_when_qt_available() -> None:
    try:
        from PyQt6.QtCore import QLocale
    except ImportError:
        return
    out = date_fmt.format_iso_date("2024-03-09")
    if QLocale.system().name() == "C":
        return
    assert out != "2024-03-09"


def test_qt_date_format_fallback_when_qt_missing(monkeypatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("PyQt6"):
            raise ImportError("simulated missing Qt")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert date_fmt.qt_date_format() == "yyyy-MM-dd"


def test_format_iso_date_fallback_when_qt_missing(monkeypatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("PyQt6"):
            raise ImportError("simulated missing Qt")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert date_fmt.format_iso_date("2024-03-09") == "2024-03-09"
