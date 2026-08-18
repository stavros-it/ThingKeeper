"""Internationalisation: tr() function with Greek and English.

A lightweight, dependency-free translation layer.  English strings are
the source keys; Greek translations live in the ``_EL`` dict.  When the
active language is ``"el"``, ``tr("File")`` returns ``"Αρχείο"``; when
``"en"`` (the default) it returns the original string unchanged.

The active language is persisted via ``QSettings`` and restored on the
next launch.
"""

from __future__ import annotations

_LANG: str = "en"
_TRANSLATIONS: dict[str, dict[str, str]] = {}

_EL: dict[str, str] = {
    # --- Menu titles ---
    "&File": "&Αρχείο",
    "&Edit": "&Επεξεργασία",
    "&View": "&Προβολή",
    "&Loans": "&Δανεισμός",
    "&Tools": "&Εργαλεία",
    "&Help": "&Βοήθεια",

    # --- File menu ---
    "&New item": "&Νέο αντικείμενο",
    "&Edit item": "&Επεξεργασία αντικειμένου",
    "&Duplicate item": "&Διπλότυπο αντικειμένου",
    "&Delete item": "&Διαγραφή αντικειμένου",
    "&Import": "&Εισαγωγή",
    "&Export": "&Εξαγωγή",
    "&Dashboard…": "&Πίνακας ελέγχου…",
    "Generate &report (PDF)…": "Δημιουργία &αναφοράς (PDF)…",
    "Custom report &builder…": "&Κατασκευαστής αναφοράς…",
    "&Quit": "&Έξοδος",

    # --- Edit menu ---
    "&Undo": "&Αναίρεση",
    "&Redo": "&Επαναφορά",
    "&Bulk edit…": "&Μαζική επεξεργασία…",

    # --- View menu ---
    "&Refresh": "&Ανανέωση",
    "&Scan serial": "&Σάρωση σειριακού",
    "&Clear filters": "&Καθαρισμός φίλτρων",
    "&Trash…": "&Κάδος…",
    "&Columns…": "&Στήλες…",

    # --- Loans menu ---
    "&Loan selected item…": "&Δανεισμός επιλεγμένου αντικειμένου…",
    "&All loans…": "&Όλα τα δάνεια…",
    "&Contacts…": "&Επαφές…",
    "Loan &history for selected…": "&Ιστορικό δανεισμού επιλεγμένου…",

    # --- Tools menu ---
    "&Back up now…": "&Δημιουργία αντιγράφου…",
    "&Restore from backup…": "&Επαναφορά από αντίγραφο…",
    "Data &integrity check…": "Έλεγχος &ακεραιότητας δεδομένων…",
    "&Settings…": "&Ρυθμίσεις…",
    "Open log &file": "Άνοιγμα &αρχείου καταγραφής",

    # --- Help menu ---
    "&About": "&Σχετικά",
    "&Keyboard shortcuts…": "&Συντομεύσεις πληκτρολογίου…",
    "&First-launch tour…": "&Παρουσίαση πρώτης εκκίνησης…",

    # --- Dialog titles (without mnemonic) ---
    "Keyboard shortcuts": "Συντομεύσεις πληκτρολογίου",
    "First-launch tour": "Παρουσίαση πρώτης εκκίνησης",
    "Action": "Ενέργεια",
    "Shortcut": "Συντόμευση",
    "Previous": "Προηγούμενο",
    "Next": "Επόμενο",
    "Finish": "Τέλος",

    # --- Toolbar ---
    "New item": "Νέο αντικείμενο",
    "Edit item": "Επεξεργασία",
    "Delete": "Διαγραφή",
    "Bulk edit": "Μαζική επεξεργασία",
    "Duplicate": "Διπλότυπο",
    "Undo": "Αναίρεση",
    "Redo": "Επαναφορά",
    "Loan": "Δανεισμός",
    "Loans": "Δανεισμοί",
    "Contacts": "Επαφές",
    "Scan": "Σάρωση",
    "Trash": "Κάδος",
    "Refresh": "Ανανέωση",
    "Dashboard": "Πίνακας",
    "Report": "Αναφορά",

    # --- Filters ---
    "Group:": "Ομάδα:",
    "Type:": "Τύπος:",
    "Brand:": "Μάρκα:",
    "Status:": "Κατάσταση:",
    "Clear": "Καθαρισμός",
    "Presets:": "Προεπιλογές:",
    "Save…": "Αποθήκευση…",
    "Search…": "Αναζήτηση…",

    # --- Dialog buttons ---
    "OK": "Εντάξει",
    "Cancel": "Άκυρο",
    "Save": "Αποθήκευση",
    "Apply": "Εφαρμογή",
    "Close": "Κλείσιμο",
    "Off": "Ανενεργό",

    # --- Common ---
    "Settings": "Ρυθμίσεις",
    "Backup folder:": "Φάκελος αντιγράφων:",
    "Browse…": "Περιήγηση…",
    "Keep last N backups:": "Διατήρηση τελευταίων N αντιγράφων:",
    "Auto-backup every:": "Αυτόματο αντίγραφο κάθε:",
    "Language:": "Γλώσσα:",
    "English": "Αγγλικά",
    "Greek": "Ελληνικά",
    "Backup folder cannot be empty.": "Ο φάκελος αντιγράφων δεν μπορεί να είναι κενός.",
    "Validation": "Επαλήθευση",
    "Please provide a borrower name.": "Παρακαλώ δώστε όνομα δανειζόμενου.",
    "Due date cannot be before the loaned date.":
        "Η ημερομηνία επιστροφής δεν μπορεί να είναι πριν τη ημερομηνία δανεισμού.",
}

_TRANSLATIONS["el"] = _EL

_SETTINGS_KEY = "ui/language"


def _load_lang() -> str:
    """Load the persisted language from QSettings (default 'en')."""
    try:
        from PyQt6.QtCore import QSettings
        s = QSettings("ThingKeeper", "ThingKeeper")
        return str(s.value(_SETTINGS_KEY, "en"))
    except Exception:  # noqa: BLE001 - QSettings may not be available in tests
        return "en"


def _save_lang(lang: str) -> None:
    try:
        from PyQt6.QtCore import QSettings
        s = QSettings("ThingKeeper", "ThingKeeper")
        s.setValue(_SETTINGS_KEY, lang)
    except Exception:  # noqa: BLE001
        pass


def set_language(lang: str) -> None:
    """Set the active language ('en' or 'el').  Persisted via QSettings."""
    global _LANG
    if lang not in ("en", "el"):
        lang = "en"
    _LANG = lang
    _save_lang(_LANG)


def get_language() -> str:
    return _LANG


def available_languages() -> list[tuple[str, str]]:
    """Return (code, display name) pairs for the UI language selector."""
    return [("en", "English"), ("el", "Ελληνικά")]


def tr(text: str) -> str:
    """Translate a string to the active language.

    English is the source language, so ``tr("File")`` returns ``"File"``
    when the language is ``en``.  When the language is ``el``, it returns
    the Greek translation from ``_EL`` (or the original English if no
    translation exists).
    """
    if _LANG == "en":
        return text
    table = _TRANSLATIONS.get(_LANG, {})
    return table.get(text, text)


_LANG = _load_lang()
