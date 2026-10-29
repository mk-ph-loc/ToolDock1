"""Πλαίσιο κειμένου + OK/Enter: clipboard + Base.txt + αρχείο θέματος. Κουμπί Notepad."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEvent, Qt
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

    def __init__(self, ctx) -> None:
        super().__init__(ctx)
        self._boxes: list[tuple[_Box, QComboBox | None]] = []

    def build_widget(self, mode: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 4, 4, 4)
        box = _Box(lambda: self.submit(box, combo))
        combo: QComboBox | None = None
        row = QHBoxLayout()
        if mode == "full":
            combo = QComboBox()
            combo.addItem("")  # χωρίς θέμα
            combo.addItems(self.ctx.cfg.get("notes.topics", []))
            combo.setCurrentText(self.ctx.cfg.get("notes.default_topic", ""))
            row.addWidget(combo, 1)
        ok = QPushButton("OK")
        ok.clicked.connect(lambda: self.submit(box, combo))
        row.addStretch(1) if combo is None else None
        row.addWidget(ok)
        lay.addWidget(box, 1)
        lay.addLayout(row)
        self._boxes.append((box, combo))
        return w

    def submit(self, box: QPlainTextEdit, combo: QComboBox | None) -> None:
        text = box.toPlainText()
        if not text.strip():
            return
        cfg = self.ctx.cfg
        topic = combo.currentText() if combo else cfg.get("notes.default_topic", "")
        if cfg.get("notes.copy_to_clipboard", True):
            QGuiApplication.clipboard().setText(text.strip())
        written = self.ctx.storage.save_note(text, topic, datetime.now())
        self.ctx.events.note_saved.emit(topic)
        self.ctx.events.status.emit("Αποθηκεύτηκε: " + (", ".join(p.name for p in written) or "μόνο clipboard"))
        if cfg.get("notes.clear_after_ok", True):
            box.clear()

    def actions(self) -> list[Action]:
        def run() -> None:
            f = self.ctx.storage.base_path if self.ctx.cfg.get("notes.notepad_opens_base", True) else None
            system.open_notepad(f)
        return [Action("notepad", "Notepad", "📝", run)]


def create(ctx) -> NotesPlugin:
    return NotesPlugin(ctx)
