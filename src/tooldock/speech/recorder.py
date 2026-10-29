"""Ηχογράφηση από μικρόφωνο με sounddevice (lazy import). Τρέχει σε worker thread."""
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


def list_input_devices() -> list[str]:
    """Ονόματα συσκευών εισόδου (κενή λίστα αν δεν υπάρχει sounddevice)."""
    if not available()[0]:
        return []
    import sounddevice as sd
    try:
        return [d["name"] for d in sd.query_devices() if d.get("max_input_channels", 0) > 0]
    except Exception:
        return []


def record(stop: threading.Event, detector: SilenceDetector, rate: int = 16000, device: str = "",
           on_level: Callable[[float], None] | None = None) -> tuple[Audio, str]:
    """Ηχογραφεί μέχρι stop.set() ή απόφαση του detector. Επιστρέφει (ήχος, λόγος τερματισμού)."""
    ok, why = available()
    if not ok:
        raise SttError(why)
    import sounddevice as sd
    q: queue.Queue[bytes] = queue.Queue()

    def cb(indata, frames, t, status) -> None:
        q.put(bytes(indata))

    chunks: list[bytes] = []
    reason = "manual"
    try:
        with sd.RawInputStream(samplerate=rate, channels=1, dtype="int16", blocksize=int(rate * 0.1),
                               device=device or None, callback=cb):
            while not stop.is_set():
                try:
                    chunk = q.get(timeout=0.2)
                except queue.Empty:
                    continue
                chunks.append(chunk)
                r = detector.feed(chunk)
                if on_level:
                    on_level(detector.level)
                if r:
                    reason = r
                    break
    except Exception as exc:
        raise SttError(f"Μικρόφωνο: {exc}") from exc
    return Audio(b"".join(chunks), rate), reason
