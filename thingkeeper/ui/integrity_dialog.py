"""Integrity check dialog: shows data/attachment problems, offers cleanup."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from .. import integrity


class IntegrityDialog(QDialog):
    """Run a data integrity check and optionally clean up orphans."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Data integrity check")
        self.resize(640, 480)
        self._build_ui()
        self._run_check()

    def _build_ui(self) -> None:
        v = QVBoxLayout(self)

        self.summary = QLabel()
        self.summary.setStyleSheet("font-weight: bold; font-size: 13px;")
        v.addWidget(self.summary)

        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        v.addWidget(self.detail, 1)

        self.cleanup_btn = QPushButton("Clean up orphan attachments")
        self.cleanup_btn.clicked.connect(self._cleanup)
        self.cleanup_btn.setEnabled(False)
        v.addWidget(self.cleanup_btn)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.reject)
        bb.accepted.connect(self.accept)
        bb.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.accept)
        v.addWidget(bb)

    def _run_check(self) -> None:
        self._report = integrity.check_integrity()
        self.summary.setText(
            "All checks passed. No problems found."
            if self._report.ok
            else f"{self._report.total()} problem(s) found."
        )
        self.summary.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: "
            + ("#1a7a1a" if self._report.ok else "#a02020")
        )
        lines: list[str] = []
        if self._report.missing_item_images:
            n = len(self._report.missing_item_images)
            lines.append(f"Missing thumbnail image (items): {n}")
            for item_id, p in self._report.missing_item_images[:20]:
                lines.append(f"  item #{item_id}: {p}")
            if len(self._report.missing_item_images) > 20:
                lines.append(f"  …and {len(self._report.missing_item_images) - 20} more")
        if self._report.missing_extra_images:
            lines.append(f"Missing extra image rows: {len(self._report.missing_extra_images)}")
            for owner, img_id, p in self._report.missing_extra_images[:20]:
                lines.append(f"  item #{owner} image_id={img_id}: {p}")
            if len(self._report.missing_extra_images) > 20:
                lines.append(f"  …and {len(self._report.missing_extra_images) - 20} more")
        if self._report.orphan_loans_item:
            lines.append(f"Loans pointing to deleted items: {len(self._report.orphan_loans_item)}")
            for loan_id, item_id in self._report.orphan_loans_item[:20]:
                lines.append(f"  loan #{loan_id} -> item #{item_id}")
        if self._report.orphan_loans_contact:
            lines.append(
                f"Loans pointing to deleted contacts: {len(self._report.orphan_loans_contact)}"
            )
            for loan_id, contact_id in self._report.orphan_loans_contact[:20]:
                lines.append(f"  loan #{loan_id} -> contact #{contact_id}")
        if self._report.orphan_attachments:
            n = len(self._report.orphan_attachments)
            lines.append(f"Orphan files in attachments folder: {n}")
            for p in self._report.orphan_attachments[:20]:
                lines.append(f"  {p}")
            if len(self._report.orphan_attachments) > 20:
                lines.append(f"  …and {len(self._report.orphan_attachments) - 20} more")

        self.detail.setPlainText("\n".join(lines))
        self.cleanup_btn.setEnabled(bool(self._report.orphan_attachments))

    def _cleanup(self) -> None:
        if not getattr(self, "_report", None):
            return
        n = self._report.orphan_attachments
        if not n:
            return
        confirm = QMessageBox.question(
            self,
            "Clean up orphans",
            f"Delete {len(n)} orphan file(s) from the attachments folder?\n"
            "This cannot be undone.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        removed = integrity.cleanup_orphan_attachments()
        # Also clear DB rows that point to missing files.
        purged = integrity.purge_missing_image_rows()
        cleared = integrity.clear_missing_item_thumbnails()
        QMessageBox.information(
            self,
            "Cleanup complete",
            f"Removed {removed} orphan file(s).\n"
            f"Purged {purged} stale image row(s).\n"
            f"Cleared {cleared} missing thumbnail(s) from items.",
        )
        self._run_check()
