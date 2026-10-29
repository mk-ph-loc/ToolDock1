"""Απλό bus σημάτων (Qt signals). Επεκτείνεται σε S2/S4 (clipboard, αναγνώριση)."""
from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    note_saved = Signal(str)       # θέμα
    activity = Signal(str, int)    # id εργαλείου, αριθμός
    status = Signal(str)           # μήνυμα γραμμής κατάστασης
