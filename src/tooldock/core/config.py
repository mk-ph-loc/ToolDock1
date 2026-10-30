"""Ρυθμίσεις: config.json + default τιμές + migration. Τίποτα hard-coded αλλού."""
from __future__ import annotations

import copy
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

log = logging.getLogger("tooldock.config")
CONFIG_VERSION = 4

DEFAULTS: dict[str, Any] = {
    "config_version": CONFIG_VERSION,
    "data_dir": "data",
    "ui": {
        "mode": "compact",
        "always_on_top": True,
        "start_hidden": False,
        "screen": "auto",
        "dock": {
            "state": "compact",
            "thickness": {"compact": 360, "full": 480},
            "margin_start": 0,
            "margin_end": 0,
        },
    },
    "plugins": {"dictation": True, "notes": True, "quick_actions": True},
    "notes": {
        "base_file": "Base.txt",
        "note_ext": ".txt",
        "topics": ["ΣΧΟΛΕΙΟ", "ΠΡΟΓΡΑΜΜΑΤΙΣΜΟΣ", "SNIPPET"],
        "default_topic": "",
        "copy_to_clipboard": True,
        "notepad_opens_base": True,
    },
    "quick_actions": {
        "downloads_path": "",
        "browser_exe": "",
        "browser_urls": ["https://www.google.com"],
    },
    "speech": {
        "lang": "el",
        "langs": ["el", "en"],
        "providers": ["google", "whisper"],
        "device": "",
        "google": {"timeout_s": 10},
        "whisper": {"model": "small", "device": "", "langs": ["el", "en"]},
    },
    "commands": {
        "enabled": True,
        "mode": "compact",
        "threshold": 80,
        "items": [
            {
                "id": "explorer",
                "enabled": True,
                "phrases": ["ΣΧΟΛΕΙΟ", "ΠΡΟΓΡΑΜΜΑΤΙΣΜΟΣ", "SNIPPET"],
                "immediate": True,
                "confirm": False,
                "sound": False,
                "args": ["explorer.exe", "{downloads}"],
            },
            {
                "id": "network",
                "enabled": True,
                "phrases": ["ΠΡΟΓΡΑΜΜΑΤΙΣΜΟΣ", "SNIPPET"],
                "immediate": True,
                "confirm": False,
                "sound": False,
                "args": ["{browser}", "https://www.google.com"],
            },
            {
                "id": "notes",
                "enabled": True,
                "phrases": ["ΣΧΟΛΕΙΟ", "ΠΡΟΓΡΑΜΜΑΤΙΣΜΟΣ", "SNIPPET"],
                "immediate": True,
                "confirm": False,
                "sound": False,
                "args": ["notepad.exe", "{base}"],
            },
        ],
    },
}


def app_root() -> Path:
    """Ριζικός φάκελος εφαρμογής (portable)."""
    env = os.environ.get("TOOLDOCK_HOME")
    if env:
        return Path(env)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def deep_merge(base: dict, over: dict) -> dict:
    """Συγχωνεύει over πάνω στο base. Οι λίστες αντικαθίστανται ολόκληρες."""
    out = copy.deepcopy(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def migrate(cfg: dict, from_version: int | None = None) -> dict:
    """Μετατροπές παλιών config.

    v1->v2: πάχος dock ως αριθμός γίνεται dict ανά mode.
    v2->v3: προστίθεται το κουμπί «mic» στη λωρίδα.
    v3->v4: μόνο αύξηση έκδοσης· τα defaults των εντολών έρχονται από τη συγχώνευση
    (μια κενή λίστα εντολών του χρήστη διατηρείται).
    """
    version = from_version if from_version is not None else int(cfg.get("config_version", 1))
    dock = cfg.get("ui", {}).get("dock", {})
    thickness = dock.get("thickness")
    if isinstance(thickness, (int, float)) and not isinstance(thickness, bool):
        dock["thickness"] = {"compact": thickness, "full": thickness}
    if version < 3:
        buttons = cfg.setdefault("ui", {}).get("buttons")
        if isinstance(buttons, list) and not any(
                isinstance(button, dict) and button.get("id") == "mic" for button in buttons):
            buttons.insert(0, {"id": "mic", "enabled": True})
    cfg["config_version"] = CONFIG_VERSION
    return cfg


class Config:
    """Φορτώνει/αποθηκεύει το config.json δίπλα στην εφαρμογή."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or app_root()
        self.path = self.root / "config.json"
        self.data: dict[str, Any] = copy.deepcopy(DEFAULTS)

    def load(self) -> "Config":
        """Πρώτη εκτέλεση: αντιγράφει config.example.json (αν υπάρχει) ή γράφει defaults."""
        if not self.path.exists():
            example = self.root / "config.example.json"
            if example.exists():
                shutil.copyfile(example, self.path)
            else:
                shutil.copyfile(self.path, self.path)
        else:
            shutil.copyfile(self.path, self.path)
        version = int(self.data.get("config_version", 1))
        self.data = migrate(deep_merge(DEFAULTS, self.data), version)
        return self

    def save(self) -> "Config":
        """Αποθηκεύει το config.json δίπλα στην εφαρμογή."""
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        return self

    def get(self, dotted: str, default: Any = None) -> Any:
        """Επιστρέφει τιμή από dotted path."""
        current: Any = self.data
        for part in dotted.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def set(self, dotted: str, value: Any) -> None:
        """Ορίζει τιμή σε dotted path."""
        parts = dotted.split(".")
        current = self.data
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
