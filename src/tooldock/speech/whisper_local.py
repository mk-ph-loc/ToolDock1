"""faster-whisper τοπικά (offline, CPU). Το μοντέλο φορτώνεται στην πρώτη χρήση."""
from __future__ import annotations

import importlib.util
import logging
import threading

from tooldock.speech.base import Audio, Provider, SttError, lang_code

log = logging.getLogger("tooldock.speech.whisper")


class WhisperProvider(Provider):
    name = "whisper"

    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self._model = None
        self._key: tuple | None = None
        self._lock = threading.Lock()

    def available(self) -> tuple[bool, str]:
        if importlib.util.find_spec("faster_whisper") is None:
            return False, "λείπει το faster-whisper (pip install -r requirements-speech.txt)"
        return True, ""

    def _load(self):
        c = self.cfg
        key = (c.get("speech.whisper.model", "small"), c.get("speech.whisper.device", "cpu"),
               c.get("speech.whisper.compute_type", "int8"))
        with self._lock:
            if self._model is None or self._key != key:
                from faster_whisper import WhisperModel  # lazy: βαριά εξάρτηση
                root = c.data_dir / c.get("speech.whisper.model_dir", "models")
                root.mkdir(parents=True, exist_ok=True)
                log.info("Φόρτωση μοντέλου Whisper %s", key)
                # ΠΡΟΣΟΧΗ: στην πρώτη χρήση κατεβαίνει το μοντέλο (~0,5–1,5 GB) και αργεί
                self._model = WhisperModel(key[0], device=key[1], compute_type=key[2], download_root=str(root))
                self._key = key
            return self._model

    def transcribe(self, audio: Audio, lang: str) -> str:
        try:
            import numpy as np
            model = self._load()
            pcm = np.frombuffer(audio.pcm, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = model.transcribe(pcm, language=lang_code(lang, "whisper"),
                                           beam_size=int(self.cfg.get("speech.whisper.beam_size", 1)),
                                           vad_filter=True)
            return " ".join(s.text.strip() for s in segments).strip()
        except SttError:
            raise
        except Exception as exc:
            raise SttError(f"faster-whisper: {exc}") from exc
