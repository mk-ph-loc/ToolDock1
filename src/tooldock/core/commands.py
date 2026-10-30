"""Μηχανή φωνητικών εντολών: ασφαλής ταύτιση και εκτέλεση χωρίς shell."""
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

from tooldock.core.textnorm import normalize

log = logging.getLogger("tooldock.commands")
try:
    from rapidfuzz import fuzz
except Exception as exc:  # lazy/προαιρετική εξάρτηση
    fuzz = None
    _IMPORT_ERROR = exc


@dataclass
class CommandMatch:
    """Αποτέλεσμα ταύτισης εντολής."""
    command: dict
    phrase: str
    score: float


class CommandEngine:
    """Ταυτίζει κείμενο με φράσεις εντολών και εκτελεί λίστα ορισμάτων."""

    def __init__(self, cfg) -> None:
        self.cfg = cfg

    def available(self) -> bool:
        """True αν η προαιρετική βιβλιοθήκη rapidfuzz είναι διαθέσιμη."""
        return fuzz is not None

    def match(self, text: str) -> CommandMatch | None:
        """Επιστρέφει την εντολή με το υψηλότερο σκορ πάνω από το κατώφλι."""
        if fuzz is None:
            raise RuntimeError("rapidfuzz δεν είναι εγκατεστημένο (requirements-commands.txt).")
        norm = normalize(text)
        if not norm:
            return None
        threshold = float(self.cfg.get("commands.threshold", 80))
        best: CommandMatch | None = None
        for command in self.cfg.get("commands.items", []):
            if not command.get("enabled", True):
                continue
            for phrase in command.get("phrases", []):
                score = float(fuzz.partial_ratio(normalize(str(phrase)), norm))
                if score >= threshold and (best is None or score > best.score):
                    best = CommandMatch(command, str(phrase), score)
        return best

    def execute(self, match: CommandMatch) -> bool:
        """Εκτελεί την ενέργεια ως λίστα ορισμάτων, χωρίς shell."""
        args = [self._resolve(argument) for argument in match.command.get("args", [])]
        if not args:
            return False
        if args[0] == "{browser}":
            from tooldock.core.system import open_urls
            open_urls([str(argument) for argument in args[1:]],
                      str(self.cfg.get("quick_actions.browser_exe", "")))
            return True
        # ΠΡΟΣΟΧΗ: τα ορίσματα προέρχονται από το config.json του χρήστη.
        subprocess.Popen(args, cwd=str(self.cfg.root))
        return True

    def _resolve(self, argument: str | object) -> str:
        """Μετατρέπει ειδικά placeholders σε πραγματικά paths."""
        value = str(argument)
        if value == "{downloads}":
            from tooldock.core.system import downloads_dir
            return str(downloads_dir(self.cfg))
        if value == "{base}":
            return str(self.cfg.data_dir / self.cfg.get("notes.base_file", "Base.txt"))
        return value
