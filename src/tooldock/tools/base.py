"""Κοινό interface plugin (σχεδιασμός §2)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget


@dataclass
class Action:
    """Κουμπί λωρίδας: id (όπως στο config ui.buttons), ετικέτα, εικονίδιο, ενέργεια."""
    id: str
    label: str
    icon: str
    run: Callable[[], None]


class Plugin:
    name: str = ""
    icon: str = ""
    enabled: bool = True

    def __init__(self, ctx) -> None:
        self.ctx = ctx

    def build_widget(self, mode: str) -> QWidget | None:
        """Widget για mode 'compact' ή 'full'· None = δεν εμφανίζεται."""
        return None

    def actions(self) -> list[Action]:
        """Κουμπιά για τη λωρίδα (mode buttons) και το full mode."""
        return []

    def on_hotkey(self) -> None:
        """Σε S4: global hotkeys."""

    def settings_schema(self) -> list[dict]:
        """Περιγραφή ρυθμίσεων (για μελλοντική αυτόματη φόρμα)."""
        return []
