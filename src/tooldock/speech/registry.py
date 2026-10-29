"""SpeechService: λίστα παρόχων με προτεραιότητα και αυτόματη εναλλαγή σε αποτυχία."""
from __future__ import annotations

import importlib
import logging
from typing import Callable

from tooldock.speech.base import Audio, Provider, SttError

log = logging.getLogger("tooldock.speech")

PROVIDERS: dict[str, tuple[str, str]] = {
    "google": ("tooldock.speech.google", "GoogleProvider"),
    "whisper": ("tooldock.speech.whisper_local", "WhisperProvider"),
}


def default_factory(name: str, cfg) -> Provider:
    """Δημιουργεί πάροχο με lazy import."""
    if name not in PROVIDERS:
        raise SttError(f"Άγνωστος πάροχος: {name}")
    mod, cls = PROVIDERS[name]
    return getattr(importlib.import_module(mod), cls)(cfg)


class SpeechService:
    """Κρατά τα instances (π.χ. φορτωμένο μοντέλο Whisper) και δοκιμάζει τους παρόχους με τη σειρά."""

    def __init__(self, cfg, factory: Callable[[str, object], Provider] | None = None) -> None:
        self.cfg = cfg
        self.factory = factory or default_factory
        self._cache: dict[str, Provider] = {}

    def _get(self, name: str) -> Provider:
        if name not in self._cache:
            self._cache[name] = self.factory(name, self.cfg)
        return self._cache[name]

    def transcribe(self, audio: Audio, lang: str,
                   on_try: Callable[[str], None] | None = None) -> tuple[str, str]:
        """Επιστρέφει (κείμενο, όνομα παρόχου). Κενό κείμενο = «δεν ακούστηκε» (όχι αποτυχία)."""
        names = [str(n) for n in self.cfg.get("speech.providers", [])]
        if not names:
            raise SttError("Δεν έχει οριστεί πάροχος (speech.providers)")
        errors: list[str] = []
        for name in names:
            try:
                prov = self._get(name)
                ok, why = prov.available()
                if not ok:
                    errors.append(f"{name}: {why}")
                    continue
                if on_try:
                    on_try(name)
                return prov.transcribe(audio, lang).strip(), name
            except SttError as exc:
                log.warning("Πάροχος %s απέτυχε: %s", name, exc)
                errors.append(f"{name}: {exc}")
        raise SttError("Απέτυχαν όλοι οι πάροχοι — " + " | ".join(errors))
