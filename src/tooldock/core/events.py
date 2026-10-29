"""Κοινό bus σημάτων εφαρμογής."""
from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    note_saved = Signal(str)
    activity = Signal(str, int)
    status = Signal(str)
    recognized = Signal(str)
