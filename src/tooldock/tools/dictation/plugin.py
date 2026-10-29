"""Υπαγόρευση: κουμπί 🎤, ηχογράφηση, πάροχοι STT, κείμενο στο πλαίσιο, el/en, κατάσταση."""
from __future__ import annotations

import logging
import threading

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
                               QVBoxLayout, QWidget)

from tooldock.speech.base import SttError
from tooldock.speech.recorder import available as mic_available, record
from tooldock.speech.registry import SpeechService
from tooldock.speech.vad import SilenceDetector
from tooldock.tools.base import Action, Plugin

log = logging.getLogger("tooldock.dictation")


class _Worker(QObject):
    """Ηχογράφηση + αναγνώριση σε worker thread. Δεν αγγίζει UI."""
    state = Signal(str)
    result = Signal(str, str)
    error = Signal(str)
    level = Signal(float)

    def __init__(self, cfg) -> None:
        super().__init__()
        self.cfg = cfg
        self.stop = threading.Event()

    def run(self) -> None:
        try:
            s = self.cfg.get("speech.silence", {})
            d = SilenceDetector(s.get("threshold", 500), s.get("stop_after_s", 1.5),
                                s.get("no_speech_timeout_s", 6.0), s.get("max_s", 60.0),
                                int(self.cfg.get("speech.sample_rate", 16000)),
                                bool(s.get("enabled", True)))
            audio, why = record(self.stop, d, int(self.cfg.get("speech.sample_rate", 16000)),
                                str(self.cfg.get("speech.device", "")), self.level.emit)
            if not audio.pcm:
                self.state.emit("done")
                self.error.emit("Δεν ακούστηκε ήχος.")
                return
            self.state.emit("transcribing")
            service = SpeechService(self.cfg)
            text, provider = service.transcribe(
                audio, str(self.cfg.get("speech.lang", "el")),
                on_try=lambda n: self.state.emit(f"transcribing:{n}"))
            self.state.emit("done")
            self.result.emit(text, provider if text else why)
        except SttError as exc:
            self.state.emit("done")
            self.error.emit(str(exc))
        except Exception:  # ΠΡΟΣΟΧΗ: απρόσμενο σφάλμα δεν πρέπει να κλείνει την εφαρμογή
            log.exception("Σφάλμα υπαγόρευσης")
            self.state.emit("done")
            self.error.emit("Απρόσμενο σφάλμα (δες logs).")


class DictationPlugin(Plugin):
    name, icon = "dictation", "🎤"

    def __init__(self, ctx) -> None:
        super().__init__(ctx)
        self._thread: QThread | None = None
        self._worker: _Worker | None = None
        self._boxes: list[QPlainTextEdit] = []

    def build_widget(self, mode: str) -> QWidget | None:
        if mode == "buttons":
            return None
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        mic = QPushButton("🎤 Υπαγόρευση")
        mic.setToolTip("Πάτησε, μίλα· σταματά αυτόματα σε σιωπή ή ξαναπάτησε.")
        mic.clicked.connect(self.toggle)
        lang = QComboBox()
        for l in self.ctx.cfg.get("speech.langs", ["el", "en"]):
            lang.addItem({"el": "Ελληνικά", "en": "English"}.get(l, l), l)
        lang.setCurrentText(str(self.ctx.cfg.get("speech.lang", "el")))
        lang.currentIndexChanged.connect(lambda: self._set_lang(lang.currentData()))
        row.addWidget(mic); row.addWidget(lang); row.addStretch(1)
        lay.addLayout(row)
        box = QPlainTextEdit()
        box.setPlaceholderText("Το αναγνωρισμένο κείμενο εμφανίζεται εδώ (επεξεργάσιμο)…")
        lay.addWidget(box, 1)
        self._boxes.append(box)
        lay.addWidget(QLabel(""))
        return w

    def _set_lang(self, lang: str) -> None:
        if lang:
            self.ctx.cfg.set("speech.lang", lang)
            self.ctx.cfg.save()

    def actions(self) -> list[Action]:
        return [Action("mic", "Υπαγόρευση", "🎤", self.toggle)]

    def toggle(self) -> None:
        if self._thread is not None:
            self._worker.stop.set()  # δεύτερο πάτημα = χειροκίνητο στοπ
            return
        ok, why = mic_available()
        if not ok:
            self.ctx.events.status.emit(f"Μικρόφωνο μη διαθέσιμο: {why}")
            return
        self.ctx.events.status.emit("Ηχογράφηση…")
        self._thread = QThread()
        self._worker = _Worker(self.ctx.cfg)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.state.connect(self._on_state)
        self._worker.result.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)
        self._thread.start()

    def _on_state(self, s: str) -> None:
        if s.startswith("transcribing"):
            p = s.split(":", 1)[1] if ":" in s else ""
            self.ctx.events.status.emit(f"Αναγνώριση… ({p})" if p else "Αναγνώριση…")
        elif s == "done":
            self.ctx.events.status.emit("Έτοιμο.")

    def _on_result(self, text: str, provider: str) -> None:
        if text:
            for b in self._boxes:
                cur = b.toPlainText()
                b.setPlainText((cur + " " if cur.strip() else "") + text)
            self.ctx.events.status.emit(f"Αναγνωρίστηκε ({provider}).")
        else:
            self.ctx.events.status.emit("Δεν αναγνωρίστηκε ομιλία.")

    def _on_error(self, msg: str) -> None:
        self.ctx.events.status.emit(msg)

    def _cleanup(self) -> None:
        if self._thread:
            self._thread.deleteLater()
        self._thread, self._worker = None, None


def create(ctx) -> DictationPlugin:
    return DictationPlugin(ctx)
