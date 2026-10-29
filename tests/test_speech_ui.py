"""Qt tests χωρίς πραγματικό μικρόφωνο ή δίκτυο."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import threading
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QPlainTextEdit
from tooldock.core.config import Config
from tooldock.core.events import EventBus
from tooldock.speech.base import Audio, SttError
from tooldock.tools.dictation import plugin as dictation
from tooldock.tools.notes.plugin import NotesPlugin


@pytest.fixture
def context(tmp_path):
    app = QApplication.instance() or QApplication([])
    cfg = Config(tmp_path)
    storage = SimpleNamespace(save_note=Mock(return_value=[]))
    return app, SimpleNamespace(cfg=cfg, storage=storage, events=EventBus())


def test_recognized_text_ok_and_clear(context):
    app, ctx = context
    notes = NotesPlugin(ctx)
    widget = notes.build_widget("compact")
    box = widget.findChild(QPlainTextEdit)
    ctx.events.recognized.emit("δοκιμή")
    assert box.toPlainText() == "δοκιμή"
    notes.submit(box, None)
    assert ctx.storage.save_note.call_args.args[0] == "δοκιμή"
    assert QApplication.clipboard().text() == "δοκιμή"
    assert box.toPlainText() == ""
    widget.close()


def test_draft_survives_mode_rebuild(context):
    app, ctx = context
    notes = NotesPlugin(ctx)
    first = notes.build_widget("compact")
    first.findChild(QPlainTextEdit).setPlainText("πρόχειρο")
    second = notes.build_widget("full")
    assert second.findChild(QPlainTextEdit).toPlainText() == "πρόχειρο"
    first.close()
    second.close()


def test_worker_finished_on_error(context, monkeypatch):
    app, ctx = context
    worker = dictation._Worker(ctx.cfg, Mock(), threading.Event())
    finished, errors = [], []
    worker.finished.connect(lambda: finished.append(True))
    worker.error.connect(errors.append)
    monkeypatch.setattr(dictation, "current_devices", Mock(side_effect=SttError("missing")))
    worker.run()
    assert finished == [True] and errors == ["missing"]


def test_worker_finished_on_success(context, monkeypatch):
    app, ctx = context
    service = Mock()
    service.transcribe.return_value = ("γεια", "fake")
    worker = dictation._Worker(ctx.cfg, service, threading.Event())
    monkeypatch.setattr(dictation, "current_devices", lambda: ([{"name": "R", "hostapi": "MME", "index": 0}], 0))
    capture = Mock(return_value=(Audio(b"\0\0" * 1600), "manual"))
    monkeypatch.setattr(dictation, "record", capture)
    finished, results = [], []
    worker.finished.connect(lambda: finished.append(True))
    worker.result.connect(lambda text, provider: results.append((text, provider)))
    worker.run()
    assert finished == [True] and results == [("γεια", "fake")]
    assert capture.call_args.args[3] == 0


def test_buttons_expand_before_record(context, monkeypatch):
    app, ctx = context
    ctx.cfg.set("ui.mode", "buttons")
    window = SimpleNamespace(ctx=ctx, set_mode=Mock(), bring_front=Mock())
    monkeypatch.setattr(dictation.QApplication, "topLevelWidgets", lambda: [window])
    monkeypatch.setattr(dictation, "mic_available", lambda: (False, "test"))
    plugin = dictation.DictationPlugin(ctx)
    plugin.toggle()
    window.set_mode.assert_called_once_with("compact")
    app.aboutToQuit.disconnect(plugin.shutdown)


def test_no_duplicate_text_widget_when_notes_enabled(context, monkeypatch):
    app, ctx = context
    monkeypatch.setattr(dictation, "mic_available", lambda: (False, "test"))
    plugin = dictation.DictationPlugin(ctx)
    widget = plugin.build_widget("compact")
    assert widget.findChildren(QPlainTextEdit) == []
    widget.close()
    app.aboutToQuit.disconnect(plugin.shutdown)
