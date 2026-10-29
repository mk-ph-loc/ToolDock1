import pytest
from tooldock.speech.base import SttError
from tooldock.speech.devices import input_devices, resolve_device, selector


@pytest.fixture
def devices():
    return input_devices([
        {"name": "Razer", "hostapi": 0, "max_input_channels": 1},
        {"name": "Output", "hostapi": 0, "max_input_channels": 0},
        {"name": "Razer", "hostapi": 1, "max_input_channels": 1},
    ], [{"name": "MME"}, {"name": "WASAPI"}])


def test_same_name_keeps_both_apis(devices):
    assert len(devices) == 2
    assert devices[1]["index"] == 2


def test_resolve_api_not_ambiguous_name(devices):
    assert resolve_device({"name": "Razer", "hostapi": "WASAPI"}, devices, 0)["index"] == 2


def test_ambiguous_old_name_is_actionable(devices):
    with pytest.raises(SttError, match="Ασαφές"):
        resolve_device("Razer", devices, 0)


def test_legacy_qualified_name(devices):
    assert resolve_device("Razer MME", devices, 0)["index"] == 0


def test_default_zero_is_valid(devices):
    assert resolve_device("", devices, 0)["index"] == 0


def test_missing_device_does_not_silently_fallback(devices):
    with pytest.raises(SttError, match="δεν είναι διαθέσιμο"):
        resolve_device({"name": "Gone", "hostapi": "MME"}, devices, 0)


def test_reenumeration_resolves_new_index(devices):
    saved = selector(devices[1])
    devices[1]["index"] = 7
    assert resolve_device(saved, devices, 0)["index"] == 7
