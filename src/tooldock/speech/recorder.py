"""Ηχογράφηση με sounddevice (lazy), με ακριβή δείκτη συσκευής."""
from __future__ import annotations

import importlib.util
import queue
import threading
from typing import Callable
from tooldock.speech.base import Audio, SttError
from tooldock.speech.vad import SilenceDetector


def available() -> tuple[bool, str]:
    if importlib.util.find_spec("sounddevice") is None:
        return False, "λείπει το sounddevice (pip install -r requirements-speech.txt)"
    return True, ""


def record(stop: threading.Event, detector: SilenceDetector, rate: int = 16000,
           device: int | str | None = None,
           on_level: Callable[[float], None] | None = None) -> tuple[Audio, str]:
    """Ηχογραφεί μέχρι χειροκίνητο στοπ ή απόφαση του detector."""
    ok, why = available()
    if not ok:
        raise SttError(why)
    import sounddevice as sd
    chunks: list[bytes] = []
    pending: queue.Queue = queue.Queue(maxsize=100)

    def callback(indata, frames, timing, status) -> None:
        try:
            pending.put_nowait((bytes(indata), bool(status)))
        except queue.Full:
            stop.set()

    reason = "manual"
    try:
        # ΠΡΟΣΟΧΗ: ο δείκτης 0 είναι έγκυρος, δεν μετατρέπεται σε None.
        selected = None if device is None or device == "" else device
        sd.check_input_settings(device=selected, samplerate=rate, channels=1, dtype="int16")
        with sd.RawInputStream(samplerate=rate, channels=1, dtype="int16", blocksize=int(rate * 0.1),
                               device=selected, callback=callback):
            while not stop.is_set():
                try:
                    chunk, overflow = pending.get(timeout=0.2)
                except queue.Empty:
                    continue
                if overflow:
                    raise SttError("Απώλεια δειγμάτων μικροφώνου. Δοκίμασε άλλο host API.")
                chunks.append(chunk)
                result = detector.feed(chunk)
                if on_level:
                    on_level(detector.level)
                if result:
                    reason = result
                    break
    except SttError:
        raise
    except Exception as exc:
        raise SttError(f"Μικρόφωνο: {exc}") from exc
    return Audio(b"".join(chunks), rate), reason
