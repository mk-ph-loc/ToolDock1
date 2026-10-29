"""Πλαίσιο κειμένου + OK/Enter: clipboard + Base.txt + αρχείο θέματος. Κουμπί Notepad."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QPlainTextEdit, QPushButton,
                               QVBoxLayout, QWidget)

from tooldock.core import system
from tooldock.tools.base import Action, Plugin


class _Box(QPlainTextEdit):
    """Enter = OK, Shift+Enter = νέα γραμμή."""

    def __init__(self, on_ok) -> None:
        super().__init__()
        self._ok = on_ok
        self.setPlaceholderText("Γράψε κείμενο… Enter = OK, Shift+Enter = νέα γραμμή")

    def keyPressEvent(self, e) -> None:
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and not (e.modifiers() & Qt.ShiftModifier):
            self._ok()
            return
        super().keyPressEvent(e)


class NotesPlugin(Plugin):
    name, icon = "notes", "📝"

    def build_widget(self, mode: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 4, 4, 4)
        combo: QComboBox | None = None
        box = _Box(lambda: self.submit(box, combo))
        row = QHBoxLayout()
        if mode == "full":
            combo = QComboBox()
            combo.addItem("")  # χωρίς θέμα
            combo.addItems(self.ctx.cfg.get("notes.topics", []))
            combo.setCurrentText(self.ctx.cfg.get("notes.default_topic", ""))
            row.addWidget(combo, 1)
        else:
            row.addStretch(1)
        ok = QPushButton("OK")
        ok.clicked.connect(lambda: self.submit(box, combo))
        row.addWidget(ok)
        lay.addWidget(box, 1)
        lay.addLayout(row)
        return w

    def submit(self, box: QPlainTextEdit, combo: QComboBox | None) -> None:
        text = box.toPlainText()
        if not text.strip():
            return
        cfg = self.ctx.cfg
        topic = combo.currentText() if combo else cfg.get("notes.default_topic", "")
        if cfg.get("notes.copy_to_clipboard", True):
            QGuiApplication.clipboard().setText(text.strip())
        now = datetime.now()
        written = self.ctx.storage.save_note(text, topic, now)
        self.ctx.events.note_saved.emit(topic)
        names = ", ".join(p.name for p in written) or "μόνο clipboard"
        self.ctx.events.status.emit(f"Αποθηκεύτηκε: {names} · {now:%Y-%m-%d %H:%M}")
        if cfg.get("notes.clear_after_ok", True):
            box.clear()

    def actions(self) -> list[Action]:
        def run() -> None:
            f = self.ctx.storage.base_path if self.ctx.cfg.get("notes.notepad_opens_base", True) else None
            system.open_notepad(f)
        return [Action("notepad", "Notepad", "📝", run)]


def create(ctx) -> NotesPlugin:
    return NotesPlugin(ctx)
