"""Υπαγόρευση: σαφής συσκευή, buttons→compact και κοινό πλαίσιο σημειώσεων."""
from __future__ import annotations

import copy
import logging
import threading
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget
from tooldock.speech.base import SttError
from tooldock.speech.devices import current_devices, label, resolve_device, selector
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

    def __init__(self, cfg, service: SpeechService, stop: threading.Event) -> None:
        super().__init__()
        self.cfg, self.service, self.stop = cfg, service, stop

    @Slot()
    def run(self) -> None:
        try:
            devices, default = current_devices()
            device = resolve_device(self.cfg.get("speech.device", ""), devices, default)
            self.state.emit(f"Ηχογράφηση… {label(device)}")
            silence = self.cfg.get("speech.silence", {})
            rate = int(self.cfg.get("speech.sample_rate", 16000))
            detector = SilenceDetector(silence.get("threshold", 500), silence.get("stop_after_s", 1.5),
                                       silence.get("no_speech_timeout_s", 6.0), silence.get("max_s", 60.0),
                                       rate, bool(silence.get("enabled", True)))
            audio, reason = record(self.stop, detector, rate, device["index"])
            if not audio.pcm or reason == "no_speech":
                self.result.emit("", "")
                return
            self.state.emit("Αναγνώριση…")
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
            # ΠΡΟΣΟΧΗ: ολοκλήρωση ακόμη και σε σφάλμα/πρόωρο return.
            self.finished.emit()


class _Bridge(QObject):
    """Δέχεται αποτελέσματα στο νήμα GUI."""
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
        self._stop = threading.Event()
        self._bridge = _Bridge(self)
        self._service = SpeechService(ctx.cfg)
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
        devices.addItem("Προεπιλεγμένο συστήματος", "")
        active = QLabel()
        active.setWordWrap(True)
        available_devices, default = [], -1
        try:
            if mic_available()[0]:
                available_devices, default = current_devices()
                for device in available_devices:
                    devices.addItem(label(device), selector(device))
        except Exception:
            log.exception("Αδυναμία απαρίθμησης μικροφώνων")
        selected = self.ctx.cfg.get("speech.device", "")
        index = devices.findData(selected)
        if index < 0:
            devices.addItem("Παλιά/μη διαθέσιμη επιλογή — επίλεξε ξανά", selected)
            index = devices.count() - 1
        devices.setCurrentIndex(index)

        def show_selection() -> None:
            try:
                device = resolve_device(devices.currentData(), available_devices, default)
                active.setText(f"Επιλεγμένο μικρόφωνο: {label(device)}")
            except SttError as exc:
                active.setText(str(exc))

        def update_device(*_) -> None:
            self.set_option("speech.device", devices.currentData())
            show_selection()

        devices.currentIndexChanged.connect(update_device)
        show_selection()
        row.addWidget(QLabel("Είσοδος:"))
        row.addWidget(devices, 1)
        layout.addLayout(row)
        layout.addWidget(active)
        if not self.ctx.cfg.get("plugins.notes", True):
            box = QPlainTextEdit()
            box.setPlainText(self._text)
            box.setPlaceholderText("Αναγνωρισμένο κείμενο (σημειώσεις απενεργοποιημένες)")
            box.textChanged.connect(lambda: setattr(self, "_text", box.toPlainText()))
            self._boxes.append(box)
            box.destroyed.connect(lambda *_: self._boxes.remove(box) if box in self._boxes else None)
            layout.addWidget(box, 1)
        return widget

    def set_option(self, key: str, value) -> None:
        self.ctx.cfg.set(key, value)
        self.ctx.cfg.save()

    def actions(self) -> list[Action]:
        return [Action("mic", "Υπαγόρευση / Στοπ", "🎤", self.toggle)]

    def toggle(self) -> None:
        if self._thread is not None:
            self._stop.set()
            return
        if not self.ctx.cfg.get("plugins.dictation", True):
            return
        if self.ctx.cfg.get("ui.mode") == "buttons" and self.ctx.cfg.get("speech.expand_on_record", True):
            for window in QApplication.topLevelWidgets():
                if getattr(window, "ctx", None) is self.ctx and hasattr(window, "set_mode"):
                    window.set_mode("compact")
                    window.bring_front()
                    break
        ok, why = mic_available()
        if not ok:
            self.ctx.events.status.emit(why)
            return
        snapshot = copy.copy(self.ctx.cfg)
        snapshot.data = copy.deepcopy(self.ctx.cfg.data)
        thread = QThread(self._bridge)
        self._stop = threading.Event()
        self._service.cfg = snapshot
        for provider in self._service._cache.values():
            provider.cfg = snapshot
        worker = _Worker(snapshot, self._service, self._stop)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.state.connect(self._bridge.status)
        worker.error.connect(self._bridge.status)
        worker.result.connect(self._bridge.result)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._bridge.cleanup)
        self._thread, self._worker = thread, worker
        self.ctx.events.status.emit("Έναρξη μικροφώνου…")
        thread.start()

    def accept_result(self, text: str, provider: str) -> None:
        if not text:
            self.ctx.events.status.emit("Δεν αναγνωρίστηκε ομιλία.")
            return
        if self.ctx.cfg.get("plugins.notes", True):
            self.ctx.events.recognized.emit(text)
        else:
            self._text = (self._text + " " if self._text.strip() else "") + text
            for box in list(self._boxes):
                box.setPlainText(self._text)
        self.ctx.events.status.emit(f"Αναγνωρίστηκε ({provider}).")

    def cleanup(self) -> None:
        if self._thread is not None:
            self._thread.deleteLater()
        self._thread, self._worker = None, None

    def shutdown(self) -> None:
        if self._thread is not None:
            # ΠΡΟΣΟΧΗ: αναμονή ολοκλήρωσης STT, όχι καταστροφή ενεργού QThread.
            self._stop.set()
            self._thread.quit()
            self._thread.wait()


def create(ctx) -> DictationPlugin:
    return DictationPlugin(ctx)
