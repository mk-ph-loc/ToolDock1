import pytest

from tooldock.speech.base import Audio, Provider, SttError, lang_code
from tooldock.speech.registry import SpeechService


class FakeCfg:
    def __init__(self, providers):
        self.d = {"speech.providers": providers}

    def get(self, k, default=None):
        return self.d.get(k, default)


class Fake(Provider):
    def __init__(self, name, text="", err=None, ok=True):
        self.name, self.text, self.err, self.ok, self.calls = name, text, err, ok, 0

    def available(self):
        return (self.ok, "" if self.ok else "λείπει")

    def transcribe(self, audio, lang):
        self.calls += 1
        if self.err:
            raise SttError(self.err)
        return self.text


def make(providers, fakes):
    return SpeechService(FakeCfg(providers), factory=lambda n, c: fakes[n])


A = Audio(b"\0\0" * 1600)


def test_first_provider_wins():
    f = {"a": Fake("a", " γεια "), "b": Fake("b", "x")}
    assert make(["a", "b"], f).transcribe(A, "el") == ("γεια", "a")
    assert f["b"].calls == 0


def test_fallback_on_error_and_unavailable():
    f = {"a": Fake("a", err="δίκτυο"), "c": Fake("c", ok=False), "b": Fake("b", "ok")}
    tried = []
    assert make(["a", "c", "b"], f).transcribe(A, "en", on_try=tried.append) == ("ok", "b")
    assert tried == ["a", "b"]


def test_empty_text_is_not_failure():
    f = {"a": Fake("a", ""), "b": Fake("b", "x")}
    assert make(["a", "b"], f).transcribe(A, "el") == ("", "a")
    assert f["b"].calls == 0


def test_all_fail_raises():
    f = {"a": Fake("a", err="e1"), "b": Fake("b", ok=False)}
    with pytest.raises(SttError) as e:
        make(["a", "b"], f).transcribe(A, "el")
    assert "e1" in str(e.value)


def test_empty_list_and_unknown_provider():
    with pytest.raises(SttError):
        make([], {}).transcribe(A, "el")
    with pytest.raises(SttError):
        SpeechService(FakeCfg(["nope"])).transcribe(A, "el")


def test_lang_code():
    assert lang_code("el", "google") == "el-GR" and lang_code("en", "whisper") == "en"
    assert lang_code("fr", "google") == "fr"
    assert round(A.seconds, 2) == 0.1
