"""Αποθήκευση σημειώσεων: Base.txt + αρχεία θεμάτων (μορφή §5 του σχεδιασμού)."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from tooldock.core.config import Config
from tooldock.core.textnorm import clean_text

log = logging.getLogger("tooldock.storage")
RULE = "────────"
_BAD = re.compile(r'[\\/:*?"<>|]')


def format_entry(text: str, topic: str, now: datetime, *, in_base: bool) -> str:
    """Κεφαλίδα + κείμενο + υπογραφή. Base: ώρα+θέμα· αρχείο θέματος: μόνο ημερομηνία."""
    stamp = now.strftime("%Y-%m-%d %H:%M")
    if in_base:
        head = f"{RULE} {stamp}" + (f" · {topic}" if topic else "") + f" {RULE}"
    else:
        head = f"{RULE} {now.strftime('%Y-%m-%d')} {RULE}"
    sig = f"[ΘΕΜΑ: {topic} · {stamp}]" if topic else f"[{stamp}]"
    return f"{head}\n{clean_text(text)}\n{sig}\n\n"


def safe_topic_name(topic: str) -> str:
    """Όνομα αρχείου από θέμα (αφαιρεί απαγορευμένους χαρακτήρες των Windows)."""
    return _BAD.sub("_", topic).strip(" .") or "ΘΕΜΑ"


class Storage:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg

    @property
    def base_path(self) -> Path:
        return self.cfg.data_dir / self.cfg.get("notes.base_file", "Base.txt")

    def topic_path(self, topic: str) -> Path:
        ext = self.cfg.get("notes.note_ext", ".txt")
        return self.cfg.data_dir / "notes" / f"{safe_topic_name(topic)}{ext}"

    def ensure_files(self) -> None:
        """Πρώτη εκτέλεση: data/, logs/, Base.txt, notes/<ΘΕΜΑ>.txt (δεν πειράζει υπάρχοντα)."""
        (self.cfg.data_dir / "notes").mkdir(parents=True, exist_ok=True)
        (self.cfg.data_dir / "logs").mkdir(exist_ok=True)
        self.base_path.touch(exist_ok=True)
        for t in self.cfg.get("notes.topics", []):
            self.topic_path(t).touch(exist_ok=True)

    @staticmethod
    def _append(path: Path, s: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(s)

    def save_note(self, text: str, topic: str = "", now: datetime | None = None) -> list[Path]:
        """Γράφει στο Base (και στο θέμα αν δόθηκε). Επιστρέφει τα αρχεία που γράφτηκαν."""
        if not clean_text(text):
            return []
        now = now or datetime.now()
        written: list[Path] = []
        if self.cfg.get("notes.write_base", True):
            self._append(self.base_path, format_entry(text, topic, now, in_base=True))
            written.append(self.base_path)
        if topic and self.cfg.get("notes.write_topic", True):
            p = self.topic_path(topic)
            self._append(p, format_entry(text, topic, now, in_base=False))
            written.append(p)
        return written
