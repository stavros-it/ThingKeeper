"""Settings dialog: backup folder, retention, auto-backup interval, language."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import backup as backup_mod
from ..i18n import available_languages, get_language, set_language, tr


class SettingsDialog(QDialog):
    """Edit ThingKeeper settings: backup location, retention, interval."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("Settings"))
        self.setMinimumWidth(480)
        self._build_ui()

    def _build_ui(self) -> None:
        v = QVBoxLayout(self)
        form = QFormLayout()

        # Backup directory.
        self.dir_edit = QLineEdit(str(backup_mod.get_backup_dir()))
        browse_btn = QPushButton(tr("Browse…"))
        browse_btn.clicked.connect(self._pick_dir)
        dir_row = QHBoxLayout()
        dir_row.addWidget(self.dir_edit, 1)
        dir_row.addWidget(browse_btn)

        dir_wrap = QWidget()
        dir_wrap.setLayout(dir_row)
        form.addRow(tr("Backup folder:"), dir_wrap)

        # Retention count.
        self.keep_spin = QSpinBox()
        self.keep_spin.setRange(1, 999)
        self.keep_spin.setValue(backup_mod.get_keep())
        form.addRow(tr("Keep last N backups:"), self.keep_spin)

        # Interval (minutes). 0 = disabled.
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(0, 24 * 60)
        self.interval_spin.setSuffix(" min")
        self.interval_spin.setSpecialValueText(tr("Off"))
        self.interval_spin.setValue(backup_mod.get_interval_minutes())
        form.addRow(tr("Auto-backup every:"), self.interval_spin)

        last = backup_mod.get_last_run()
        last_label = QLabel(f"Last backup: {last or 'never'}")
        last_label.setStyleSheet("color: #9a9a9a;")
        form.addRow("", last_label)

        # Language selector.
        self.lang_combo = QComboBox()
        current_lang = get_language()
        for code, name in available_languages():
            self.lang_combo.addItem(name, code)
        idx = self.lang_combo.findData(current_lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        form.addRow(tr("Language:"), self.lang_combo)

        v.addLayout(form)

        # Buttons.
        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        bb.button(QDialogButtonBox.StandardButton.Save).setText(tr("Save"))
        bb.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("Cancel"))
        bb.accepted.connect(self._save)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _pick_dir(self) -> None:
        cur = self.dir_edit.text().strip() or str(backup_mod._default_backup_dir())
        d = QFileDialog.getExistingDirectory(self, "Backup folder", cur)
        if d:
            self.dir_edit.setText(d)

    def _save(self) -> None:
        raw = self.dir_edit.text().strip()
        if not raw:
            QMessageBox.warning(self, tr("Settings"), tr("Backup folder cannot be empty."))
            return
        p = Path(raw)
        try:
            p.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.warning(
                self, tr("Settings"),
                f"Cannot create or write to folder:\n{exc}",
            )
            return
        backup_mod.set_backup_dir(p)
        backup_mod.set_keep(self.keep_spin.value())
        backup_mod.set_interval_minutes(self.interval_spin.value())
        new_lang = self.lang_combo.currentData()
        set_language(new_lang)
        parent = self.parent()
        if parent is not None:
            QCoreApplication.postEvent(
                parent, QEvent(QEvent.Type.LanguageChange)
            )
        self.accept()
