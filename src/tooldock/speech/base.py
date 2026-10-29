"""Κοινό interface παρόχων STT, τύπος ήχου, σφάλματα και αντιστοίχιση γλώσσας."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

LANGS: dict[str, dict[str, str]] = {
    "el": {"google": "el-GR", "whisper": "el"},
    "en": {"google": "en-US", "whisper": "en"},
}


def lang_code(lang: str, kind: str) -> str:
    """Κωδικός γλώσσας για το είδος παρόχου ('google' | 'whisper')."""
    return LANGS.get(lang, {}).get(kind, lang)


class SttError(Exception):
    """Αποτυχία παρόχου — ο service δοκιμάζει τον επόμενο."""


@dataclass
class Audio:
    """Ήχος PCM int16, mono (little-endian)."""
    pcm: bytes
    rate: int = 16000

    @property
    def seconds(self) -> float:
        return len(self.pcm) / 2 / self.rate if self.rate else 0.0


class Provider(ABC):
    """Interface παρόχου: transcribe(audio, lang) -> κείμενο (κενό = δεν αναγνωρίστηκε ομιλία)."""
    name: str = ""

    @abstractmethod
    def available(self) -> tuple[bool, str]:
        """(True, '') αν οι εξαρτήσεις υπάρχουν, αλλιώς (False, οδηγία εγκατάστασης)."""

    @abstractmethod
    def transcribe(self, audio: Audio, lang: str) -> str:
        """Αναγνώριση. Ρίχνει SttError σε αποτυχία."""
