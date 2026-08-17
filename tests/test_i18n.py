"""Tests for thingkeeper.i18n: tr() function and language switching."""

from __future__ import annotations

from thingkeeper import i18n


def test_default_language_is_english():
    i18n.set_language("en")
    assert i18n.get_language() == "en"


def test_set_language_greek():
    i18n.set_language("el")
    assert i18n.get_language() == "el"


def test_tr_returns_original_in_english():
    i18n.set_language("en")
    assert i18n.tr("&File") == "&File"


def test_tr_translates_to_greek():
    i18n.set_language("el")
    assert i18n.tr("&File") == "&Αρχείο"
    assert i18n.tr("&Edit") == "&Επεξεργασία"
    assert i18n.tr("&Help") == "&Βοήθεια"
    assert i18n.tr("&Quit") == "&Έξοδος"


def test_tr_falls_back_for_unknown_string():
    i18n.set_language("el")
    assert i18n.tr("nonexistent string") == "nonexistent string"


def test_tr_falls_back_to_english_after_switch():
    i18n.set_language("el")
    assert i18n.tr("&File") == "&Αρχείο"
    i18n.set_language("en")
    assert i18n.tr("&File") == "&File"


def test_available_languages_returns_both():
    langs = i18n.available_languages()
    codes = [code for code, _ in langs]
    assert "en" in codes
    assert "el" in codes


def test_set_invalid_language_defaults_to_english():
    i18n.set_language("fr")
    assert i18n.get_language() == "en"
