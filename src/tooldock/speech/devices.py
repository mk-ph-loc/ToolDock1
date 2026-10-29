"""Σταθερή ταυτότητα εισόδου: όνομα + host API, όχι αποθηκευμένος δείκτης."""
from __future__ import annotations

from tooldock.speech.base import SttError


def input_devices(devices: list, hostapis: list) -> list[dict]:
    """Κρατά κάθε είσοδο ξεχωριστή, ακόμη και αν τα ονόματα συμπίπτουν."""
    return [{"index": i, "name": d["name"], "hostapi": hostapis[d["hostapi"]]["name"]}
            for i, d in enumerate(devices) if d["max_input_channels"] > 0]


def selector(device: dict) -> dict[str, str]:
    return {"name": device["name"], "hostapi": device["hostapi"]}


def label(device: dict) -> str:
    return f'{device["name"]} — {device["hostapi"]} [#{device["index"]}]'


def resolve_device(selection, devices: list[dict], default_index: int) -> dict:
    """Επιλύει αποθηκευμένη επιλογή στον τρέχοντα δείκτη. Η ασάφεια δεν αγνοείται."""
    if selection in (None, ""):
        matches = [d for d in devices if d["index"] == default_index]
    elif isinstance(selection, dict):
        matches = [d for d in devices if selector(d) == selection]
    elif isinstance(selection, str):
        # Συμβατότητα παλιών config: σκέτο όνομα ή όνομα μαζί με host API.
        matches = [d for d in devices if selection in (d["name"], f'{d["name"]} {d["hostapi"]}')]
    else:
        matches = []
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SttError("Ασαφές μικρόφωνο: επίλεξε συσκευή μαζί με host API από τη λίστα.")
    raise SttError("Το επιλεγμένο μικρόφωνο δεν είναι διαθέσιμο. Επίλεξε ξανά από τη λίστα.")


def current_devices() -> tuple[list[dict], int]:
    """Lazy πρόσβαση στο sounddevice· δεν φορτώνεται με την εισαγωγή του module."""
    import sounddevice as sd
    return input_devices(sd.query_devices(), sd.query_hostapis()), int(sd.default.device[0])
