"""Υπαγόρευση με worker και επιλογή συσκευής εισόδου."""
from __future__ import annotations

import copy
import logging
import threading

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from tooldock.speech.base import SttError
from tooldock.speech.recorder import available as mic_available, record
from tooldock.speech.registry import SpeechService
from tooldock.speech.vad import SilenceDetector
from tooldock.tools.base import Action, Plugin

log = logging.getLogger("tooldock.dictation")


class _Worker(QObject):
    state = Signal(str)
    result = Signal(str, str)
    error = Signal(str)
    finished = Signal()

    def __init__(self, cfg, service: SpeechService) -> None:
        super().__init__()
        self.cfg, self.service = cfg, service
        self.stop = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            s = self.cfg.get("speech.silence", {})
            rate = int(self.cfg.get("speech.sample_rate", 16000))
            detector = SilenceDetector(s.get("threshold", 500), s.get("stop_after_s", 1.5),
                                       s.get("no_speech_timeout_s", 6.0), s.get("max_s", 60.0),
                                       rate, bool(s.get("enabled", True)))
            audio, reason = record(self.stop, detector, rate, str(self.cfg.get("speech.device", "")))
            if not audio.pcm or reason == "no_speech":
                self.result.emit("", "")
                return
            text, provider = self.service.transcribe(
                audio, str(self.cfg.get("speech.lang", "el")),
                on_try=lambda name: self.state.emit(f"Αναγνώριση… ({name})"))
            self.result.emit(text, provider)
        except SttError as exc:
            self.error.emit(str(exc))
        except Exception:
            log.exception("Σφάλμα υπαγόρευσης")
            self.error.emit("Σφάλμα υπαγόρευσης (δες logs).")
        finally:
            # ΠΡΟΣΟΧΗ: εκπέμπεται πάντα, ακόμη και μετά από σφάλμα ή πρόωρο return.
            self.finished.emit()


class _Bridge(QObject):
    """Δρομολόγηση αποτελεσμάτων στο νήμα GUI, όχι στο worker."""
    def __init__(self, plugin) -> None:
        super().__init__()
        self.plugin = plugin

    @Slot(str)
    def status(self, message: str) -> None:
        self.plugin.ctx.events.status.emit(message)

    @Slot(str, str)
    def result(self, text: str, provider: str) -> None:
        self.plugin.accept_result(text, provider)

    @Slot()
    def cleanup(self) -> None:
        self.plugin.cleanup()


class DictationPlugin(Plugin):
    name, icon = "dictation", "🎤"

    def __init__(self, ctx) -> None:
        super().__init__(ctx)
        self._thread: QThread | None = None
        self._worker: _Worker | None = None
        self._bridge = _Bridge(self)
        self._text = ""
        self._boxes: list[QPlainTextEdit] = []
        QApplication.instance().aboutToQuit.connect(self.shutdown)

    def build_widget(self, mode: str) -> QWidget | None:
        if mode == "buttons":
            return None
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        lang = QComboBox()
        for code in self.ctx.cfg.get("speech.langs", ["el", "en"]):
            lang.addItem({"el": "Ελληνικά", "en": "English"}.get(code, code), code)
        lang.setCurrentIndex(max(0, lang.findData(self.ctx.cfg.get("speech.lang", "el"))))
        lang.currentIndexChanged.connect(lambda *_: self.set_option("speech.lang", lang.currentData()))
        row.addWidget(lang)
        devices = QComboBox()
        devices.setMinimumContentsLength(12)
        devices.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        active = QLabel()
        active.setWordWrap(True)
        devices.addItem("Προεπιλεγμένο συστήματος", "")
        default_name = "μη διαθέσιμο"
        if mic_available()[0]:
            try:
                import sounddevice as sd  # προαιρετική εξάρτηση
                default_name = sd.query_devices(kind="input")["name"]
                seen: set[str] = set()
                for device in sd.query_devices():
                    name = device["name"]
                    if device["max_input_channels"] > 0 and name not in seen:
                        devices.addItem(name, name)
                        seen.add(name)
            except Exception:
                log.exception("Αδυναμία απαρίθμησης μικροφώνων")
        selected = self.ctx.cfg.get("speech.device", "")
        index = devices.findData(selected)
        if index < 0:
            devices.addItem(f"Μη διαθέσιμο: {selected}", selected)
            index = devices.count() - 1
        devices.setCurrentIndex(index)

        def update_device(*_) -> None:
            value = devices.currentData()
            self.set_option("speech.device", value)
            active.setText(f"Μικρόφωνο: {value or default_name}")

        devices.currentIndexChanged.connect(update_device)
        active.setText(f"Μικρόφωνο: {selected or default_name}")
        row.addWidget(QLabel("Είσοδος:"))
        row.addWidget(devices, 1)
        layout.addLayout(row)
        layout.addWidget(active)
        box = QPlainTextEdit()
        box.setPlaceholderText("Αναγνωρισμένο κείμενο (επεξεργάσιμο)…")
        box.setPlainText(self._text)
        box.textChanged.connect(lambda: setattr(self, "_text", box.toPlainText()))
        self._boxes.append(box)
        box.destroyed.connect(lambda *_: self._boxes.remove(box) if box in self._boxes else None)
        layout.addWidget(box, 1)
        return widget

    def set_option(self, key: str, value) -> None:
        self.ctx.cfg.set(key, value)
        self.ctx.cfg.save()

    def actions(self) -> list[Action]:
        # Ένα μόνο κουμπί: αυτό που κατασκευάζει το Shell στη λωρίδα.
        return [Action("mic", "Υπαγόρευση / Στοπ", "🎤", self.toggle)]

    def toggle(self) -> None:
        if self._thread is not None:
            if self._worker is not None:
                self._worker.stop.set()
            return
        ok, why = mic_available()
        if not ok:
            self.ctx.events.status.emit(why)
            return
        if not self.ctx.cfg.get("plugins.dictation", True):
            return
        snapshot = copy.copy(self.ctx.cfg)
        snapshot.data = copy.deepcopy(self.ctx.cfg.data)
        thread = QThread(self._bridge)
        worker = _Worker(snapshot, SpeechService(snapshot))
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.state.connect(self._bridge.status)
        worker.error.connect(self._bridge.status)
        worker.result.connect(self._bridge.result)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._bridge.cleanup)
        self._thread, self._worker = thread, worker
        self.ctx.events.status.emit("Ηχογράφηση…")
        thread.start()

    def accept_result(self, text: str, provider: str) -> None:
        if text:
            self._text = (self._text + " " if self._text.strip() else "") + text
            for box in list(self._boxes):
                box.setPlainText(self._text)
            self.ctx.events.status.emit(f"Αναγνωρίστηκε ({provider}).")
        else:
            self.ctx.events.status.emit("Δεν αναγνωρίστηκε ομιλία.")

    def cleanup(self) -> None:
        if self._thread is not None:
            self._thread.deleteLater()
        self._thread, self._worker = None, None

    def shutdown(self) -> None:
        # ΠΡΟΣΟΧΗ: δεν καταστρέφουμε QThread όσο εκτελείται αναγνώριση.
        if self._thread is not None:
            try:
                if self._worker is not None:
                    self._worker.stop.set()
            except RuntimeError:
                pass
            self._thread.quit()
            self._thread.wait()


def create(ctx) -> DictationPlugin:
    return DictationPlugin(ctx)
