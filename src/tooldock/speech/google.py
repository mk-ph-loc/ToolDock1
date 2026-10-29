"""Google Web Speech (μέσω SpeechRecognition). Online, ανεπίσημο API, χωρίς κλειδί."""
from __future__ import annotations

import importlib.util

from tooldock.speech.base import Audio, Provider, SttError, lang_code


class GoogleProvider(Provider):
    name = "google"

    def __init__(self, cfg) -> None:
        self.cfg = cfg

    def available(self) -> tuple[bool, str]:
        if importlib.util.find_spec("speech_recognition") is None:
            return False, "λείπει το πακέτο SpeechRecognition (pip install -r requirements-speech.txt)"
        return True, ""

    def transcribe(self, audio: Audio, lang: str) -> str:
        import speech_recognition as sr  # lazy: φορτώνεται μόνο όταν χρησιμοποιηθεί
        rec = sr.Recognizer()
        rec.operation_timeout = float(self.cfg.get("speech.google.timeout_s", 10))
        data = sr.AudioData(audio.pcm, audio.rate, 2)
        try:
            return rec.recognize_google(data, language=lang_code(lang, "google"))
        except sr.UnknownValueError:
            return ""
        except (sr.RequestError, OSError) as exc:
            raise SttError(f"Google Web Speech: {exc}") from exc
