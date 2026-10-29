"""Κοινό πλαίσιο κειμένου/υπαγόρευσης και OK/Enter."""
from __future__ import annotations

from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget
from tooldock.core import system
from tooldock.tools.base import Action, Plugin


class _Box(QPlainTextEdit):
    def __init__(self, on_ok) -> None:
        super().__init__()
        self._ok = on_ok
        self.setPlaceholderText("Γράψε ή υπαγόρευσε… Enter = OK, Shift+Enter = νέα γραμμή")

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self._ok()
            return
        super().keyPressEvent(event)


class NotesPlugin(Plugin):
    name, icon = "notes", "📝"

    def __init__(self, ctx) -> None:
        super().__init__(ctx)
        self._text = ""
        self._boxes: list[QPlainTextEdit] = []
        ctx.events.recognized.connect(self.append_text)

    def _sync(self, text: str) -> None:
        self._text = text
        for box in list(self._boxes):
            if box.toPlainText() != text:
                box.blockSignals(True)
                box.setPlainText(text)
                box.blockSignals(False)

    def append_text(self, text: str) -> None:
        self._sync((self._text.rstrip() + " " if self._text.strip() else "") + text)

    def build_widget(self, mode: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        combo = None
        if mode == "full":
            combo = QComboBox()
            combo.addItem("")
            combo.addItems(self.ctx.cfg.get("notes.topics", []))
            combo.setCurrentText(self.ctx.cfg.get("notes.default_topic", ""))
        box = _Box(lambda: self.submit(box, combo))
        box.setPlainText(self._text)
        self._boxes.append(box)
        box.textChanged.connect(lambda: self._sync(box.toPlainText()))
        box.destroyed.connect(lambda *_: self._boxes.remove(box) if box in self._boxes else None)
        row = QHBoxLayout()
        if combo is not None:
            row.addWidget(combo, 1)
        else:
            row.addStretch(1)
        ok = QPushButton("OK")
        ok.clicked.connect(lambda: self.submit(box, combo))
        row.addWidget(ok)
        layout.addWidget(box, 1)
        layout.addLayout(row)
        return widget

    def submit(self, box: QPlainTextEdit, combo: QComboBox | None) -> None:
        text = box.toPlainText()
        if not text.strip():
            return
        cfg = self.ctx.cfg
        topic = combo.currentText() if combo is not None else cfg.get("notes.default_topic", "")
        if cfg.get("notes.copy_to_clipboard", True):
            QGuiApplication.clipboard().setText(text.strip())
        now = datetime.now()
        written = self.ctx.storage.save_note(text, topic, now)
        self.ctx.events.note_saved.emit(topic)
        names = ", ".join(path.name for path in written) or "μόνο clipboard"
        self.ctx.events.status.emit(f"Αποθηκεύτηκε: {names} · {now:%Y-%m-%d %H:%M}")
        if cfg.get("notes.clear_after_ok", True):
            self._sync("")

    def actions(self) -> list[Action]:
        def run() -> None:
            path = self.ctx.storage.base_path if self.ctx.cfg.get("notes.notepad_opens_base", True) else None
            system.open_notepad(path)
        return [Action("notepad", "Notepad", "📝", run)]


def create(ctx) -> NotesPlugin:
    return NotesPlugin(ctx)
