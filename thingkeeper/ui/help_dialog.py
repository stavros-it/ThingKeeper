"""In-app help: keyboard shortcut cheatsheet and first-launch tour.

Both dialogs are translated via :mod:`thingkeeper.i18n`.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..i18n import tr

_SHORTCUTS_EN: list[tuple[str, str]] = [
    ("New item", "Ctrl+N"),
    ("Edit item", "Ctrl+E"),
    ("Duplicate item", "Ctrl+D"),
    ("Delete item", "Delete"),
    ("Undo", "Ctrl+Z"),
    ("Redo", "Ctrl+Y"),
    ("Bulk edit", "Ctrl+B"),
    ("Loan item", "Ctrl+L"),
    ("Scan serial", "Ctrl+K"),
    ("Refresh", "F5"),
    ("Generate PDF report", "Ctrl+R"),
    ("Find / focus search", "Ctrl+F"),
    ("Keyboard shortcuts", "F1"),
    ("Quit", "Ctrl+Q"),
]

_SHORTCUTS_EL: list[tuple[str, str]] = [
    ("Νέο αντικείμενο", "Ctrl+N"),
    ("Επεξεργασία αντικειμένου", "Ctrl+E"),
    ("Διπλότυπο αντικειμένου", "Ctrl+D"),
    ("Διαγραφή αντικειμένου", "Delete"),
    ("Αναίρεση", "Ctrl+Z"),
    ("Επαναφορά", "Ctrl+Y"),
    ("Μαζική επεξεργασία", "Ctrl+B"),
    ("Δανεισμός αντικειμένου", "Ctrl+L"),
    ("Σάρωση σειριακού", "Ctrl+K"),
    ("Ανανέωση", "F5"),
    ("Δημιουργία αναφοράς PDF", "Ctrl+R"),
    ("Εύρεση / εστίαση αναζήτησης", "Ctrl+F"),
    ("Συντομεύσεις πληκτρολογίου", "F1"),
    ("Έξοδος", "Ctrl+Q"),
]


class ShortcutsDialog(QDialog):
    """Modal dialog showing all keyboard shortcuts in a 2-column table."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("Keyboard shortcuts"))
        self.setMinimumSize(460, 520)
        self._build_ui()

    def _build_ui(self) -> None:
        v = QVBoxLayout(self)

        title = QLabel(tr("Keyboard shortcuts"))
        f = title.font()
        f.setPointSize(14)
        f.setBold(True)
        title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(title)

        from ..i18n import get_language
        rows = _SHORTCUTS_EL if get_language() == "el" else _SHORTCUTS_EN
        table = QTableWidget(len(rows), 2)
        table.setHorizontalHeaderLabels([tr("Action"), tr("Shortcut")])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.horizontalHeader().setStretchLastSection(False)
        table.setColumnWidth(0, 300)
        table.setColumnWidth(1, 140)
        for r, (action, shortcut) in enumerate(rows):
            a = QTableWidgetItem(action)
            a.setFlags(a.flags() & ~Qt.ItemFlag.ItemIsEditable)
            s = QTableWidgetItem(shortcut)
            s.setFlags(s.flags() & ~Qt.ItemFlag.ItemIsEditable)
            s.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(r, 0, a)
            table.setItem(r, 1, s)
        v.addWidget(table)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.button(QDialogButtonBox.StandardButton.Close).setText(tr("Close"))
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)


_TOUR_STEPS_EN: list[tuple[str, str]] = [
    ("Welcome to ThingKeeper",
     "ThingKeeper is a desktop inventory app for gadgets, appliances, "
     "and hardware parts. This short tour highlights the main features."),
    ("Add items",
     "Click 'New item' on the toolbar (or press Ctrl+N) to add a new "
     "thing to your inventory. Fill in group, type, brand, model, "
     "serial number, and other details."),
    ("Search and filter",
     "Use the search box at the top to find items by keyword. "
     "Use the dropdown filters to narrow by Group, Type, Brand, or Status."),
    ("Edit, duplicate, delete",
     "Select a row and use the toolbar (or the Edit menu) to edit, "
     "duplicate, or delete items. Double-click a row to edit it directly."),
    ("Loans",
     "Mark items as 'LOANED' and track who has them. Use the Loans "
     "menu to manage loans and contacts."),
    ("Dashboard and reports",
     "Open the Dashboard from the toolbar (or File > Dashboard) to see "
     "charts of your inventory. Generate PDF reports from File > Generate report."),
    ("Backups and settings",
     "ThingKeeper auto-backs up to a local folder. Configure backup "
     "frequency and folder in Tools > Settings. You can also switch "
     "the UI language between English and Greek there."),
    ("Help",
     "Press F1 at any time to see the keyboard shortcut cheatsheet. "
     "You can replay this tour from Help > First-launch tour."),
]

_TOUR_STEPS_EL: list[tuple[str, str]] = [
    ("Καλώς ήρθατε στο ThingKeeper",
     "Το ThingKeeper είναι μια εφαρμογή διαχείρισης αποθέματος για "
     "συσκευές, συσκευές οικιακής χρήσης και εξαρτήματα. Αυτή η σύντομη "
     "παρουσίαση αναδεικνύει τα κύρια χαρακτηριστικά."),
    ("Προσθήκη αντικειμένων",
     "Κάντε κλικ στο 'Νέο αντικείμενο' στη γραμμή εργαλείων (ή πατήστε "
     "Ctrl+N) για να προσθέσετε ένα νέο αντικείμενο στο απόθεμά σας. "
     "Συμπληρώστε ομάδα, τύπο, μάρκα, μοντέλο, σειριακό αριθμό και άλλες "
     "λεπτομέρειες."),
    ("Αναζήτηση και φιλτράρισμα",
     "Χρησιμοποιήστε το πλαίσιο αναζήτησης στην κορυφή για να βρείτε "
     "αντικείμενα με λέξη-κλειδί. Χρησιμοποιήστε τα φίλτρα αναπτυσσόμενων "
     "μενού για να περιορίσετε ανά Ομάδα, Τύπο, Μάρκα ή Κατάσταση."),
    ("Επεξεργασία, διπλότυπο, διαγραφή",
     "Επιλέξτε μια γραμμή και χρησιμοποιήστε τη γραμμή εργαλείων (ή το "
     "μενού Επεξεργασία) για να επεξεργαστείτε, να αντιγράψετε ή να "
     "διαγράψετε αντικείμενα. Διπλό κλικ σε μια γραμμή για άμεση επεξεργασία."),
    ("Δανεισμός",
     "Μαρκάρετε αντικείμενα ως 'LOANED' και παρακολουθήστε ποια τα έχει. "
     "Χρησιμοποιήστε το μενού Δανεισμός για διαχείριση δανεισμών και επαφών."),
    ("Πίνακας ελέγχου και αναφορές",
     "Ανοίξτε τον Πίνακα ελέγχου από τη γραμμή εργαλείων (ή Αρχείο > "
     "Πίνακας ελέγχου) για να δείτε διαγράμματα του αποθέματός σας. "
     "Δημιουργήστε αναφορές PDF από Αρχείο > Δημιουργία αναφοράς."),
    ("Αντίγραφα και ρυθμίσεις",
     "Το ThingKeeper δημιουργεί αυτόματα αντίγραφα ασφαλείας σε τοπικό "
     "φάκελο. Ρυθμίστε τη συχνότητα και τον φάκελο στα Εργαλεία > Ρυθμίσεις. "
     "Εκεί μπορείτε επίσης να αλλάξετε γλώσσα διεπαφής μεταξύ Αγγλικών και "
     "Ελληνικών."),
    ("Βοήθεια",
     "Πατήστε F1 οποιαδήποτε στιγμή για να δείτε τις συντομεύσεις "
     "πληκτρολογίου. Μπορείτε να αναπαράγετε αυτή την παρουσίαση από "
     "Βοήθεια > Παρουσίαση πρώτης εκκίνησης."),
]


class TourDialog(QDialog):
    """Multi-step first-launch tour with Next/Previous navigation."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("First-launch tour"))
        self.setMinimumSize(540, 320)
        from ..i18n import get_language
        self._steps = _TOUR_STEPS_EL if get_language() == "el" else _TOUR_STEPS_EN
        self._index = 0
        self._build_ui()
        self._render()

    def _build_ui(self) -> None:
        v = QVBoxLayout(self)

        self.title_label = QLabel()
        f = self.title_label.font()
        f.setPointSize(15)
        f.setBold(True)
        self.title_label.setFont(f)
        self.title_label.setWordWrap(True)
        v.addWidget(self.title_label)

        self.body_label = QLabel()
        self.body_label.setWordWrap(True)
        self.body_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        v.addWidget(self.body_label, 1)

        self.progress_label = QLabel()
        self.progress_label.setStyleSheet("color: #9a9a9a;")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.progress_label)

        nav = QHBoxLayout()
        self.prev_btn = QPushButton(tr("Previous"))
        self.prev_btn.clicked.connect(self._prev)
        self.next_btn = QPushButton(tr("Next"))
        self.next_btn.clicked.connect(self._next)
        self.finish_btn = QPushButton(tr("Close"))
        self.finish_btn.clicked.connect(self.accept)
        nav.addWidget(self.prev_btn)
        nav.addStretch(1)
        nav.addWidget(self.next_btn)
        nav.addWidget(self.finish_btn)
        v.addLayout(nav)

    def _render(self) -> None:
        title, body = self._steps[self._index]
        self.title_label.setText(title)
        self.body_label.setText(body)
        n = len(self._steps)
        self.progress_label.setText(f"{self._index + 1} / {n}")
        self.prev_btn.setEnabled(self._index > 0)
        is_last = self._index == n - 1
        self.next_btn.setVisible(not is_last)
        self.finish_btn.setVisible(is_last)
        if is_last:
            self.finish_btn.setText(tr("Finish"))

    def _prev(self) -> None:
        if self._index > 0:
            self._index -= 1
            self._render()

    def _next(self) -> None:
        if self._index < len(self._steps) - 1:
            self._index += 1
            self._render()
