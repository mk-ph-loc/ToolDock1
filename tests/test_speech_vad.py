from array import array

from tooldock.speech.vad import SilenceDetector, rms


def chunk(amp: int, ms: int = 100, rate: int = 16000) -> bytes:
    return array("h", [amp, -amp] * (rate * ms // 1000 // 2)).tobytes()


def test_rms_silence_and_loud():
    assert rms(b"") == 0.0
    assert rms(chunk(0)) == 0.0
    assert abs(rms(chunk(1000)) - 1000) < 1


def test_stops_after_silence_following_speech():
    d = SilenceDetector(threshold=500, stop_after_s=0.5, rate=16000)
    assert d.feed(chunk(2000)) is None and d.heard_speech
    res = [d.feed(chunk(0)) for _ in range(5)]
    assert res[:4] == [None] * 4 and res[4] == "silence"


def test_no_speech_timeout():
    d = SilenceDetector(threshold=500, no_speech_timeout_s=0.3)
    res = [d.feed(chunk(10)) for _ in range(3)]
    assert res == [None, None, "no_speech"] and not d.heard_speech


def test_disabled_only_max():
    d = SilenceDetector(enabled=False, max_s=0.3)
    assert [d.feed(chunk(0)) for _ in range(3)] == [None, None, "max"]
