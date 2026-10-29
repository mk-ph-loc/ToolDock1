"""Ανίχνευση σιωπής με RMS (χωρίς numpy). Καθαρή λογική, με tests."""
from __future__ import annotations

import math
from array import array


def rms(pcm: bytes) -> float:
    """Ενεργός τιμή (RMS) δείγματος int16."""
    a = array("h")
    a.frombytes(pcm[: len(pcm) // 2 * 2])
    if not a:
        return 0.0
    return math.sqrt(sum(x * x for x in a) / len(a))


class SilenceDetector:
    """Δέχεται κομμάτια PCM και λέει πότε να σταματήσει η ηχογράφηση.

    feed() -> None (συνέχισε) | "silence" | "no_speech" | "max".
    """

    def __init__(self, threshold: float = 500, stop_after_s: float = 1.5,
                 no_speech_timeout_s: float = 6.0, max_s: float = 60.0,
                 rate: int = 16000, enabled: bool = True) -> None:
        self.threshold, self.stop_after_s = float(threshold), float(stop_after_s)
        self.no_speech_timeout_s, self.max_s = float(no_speech_timeout_s), float(max_s)
        self.rate, self.enabled = int(rate), enabled
        self.elapsed = 0.0
        self.silent = 0.0
        self.heard_speech = False
        self.level = 0.0

    def feed(self, pcm: bytes) -> str | None:
        dt = len(pcm) / 2 / self.rate
        self.elapsed += dt
        self.level = rms(pcm)
        if self.level >= self.threshold:
            self.heard_speech, self.silent = True, 0.0
        else:
            self.silent += dt
        if self.elapsed >= self.max_s:
            return "max"
        if self.enabled:
            if self.heard_speech and self.silent >= self.stop_after_s:
                return "silence"
            if not self.heard_speech and self.elapsed >= self.no_speech_timeout_s:
                return "no_speech"
        return None
