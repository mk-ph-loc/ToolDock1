"""Έλεγχος πολιτικής ύψους με και χωρίς ενεργές σημειώσεις."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from types import SimpleNamespace
import pytest
pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QSizePolicy
from tooldock.core.config import Config
from tooldock.core.events import EventBus
from tooldock.tools.dictation import plugin as dictation


@pytest.mark.parametrize("notes_enabled", [True, False])
def test_controls_height_policy(tmp_path, monkeypatch, notes_enabled):
    app = QApplication.instance() or QApplication([])
    cfg = Config(tmp_path)
    cfg.set("plugins.notes", notes_enabled)
    ctx = SimpleNamespace(cfg=cfg, events=EventBus())
    monkeypatch.setattr(dictation, "mic_available", lambda: (False, "test"))
    plugin = dictation.DictationPlugin(ctx)
    widget = plugin.build_widget("compact")
    try:
        if notes_enabled:
            assert widget.sizePolicy().verticalPolicy() == QSizePolicy.Maximum
            assert not widget.findChildren(QPlainTextEdit)
        else:
            assert widget.sizePolicy().verticalPolicy() != QSizePolicy.Maximum
            assert len(widget.findChildren(QPlainTextEdit)) == 1
    finally:
        app.aboutToQuit.disconnect(plugin.shutdown)
        widget.close()
        widget.deleteLater()
