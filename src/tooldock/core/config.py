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
            "state": "float",
            "thickness": {"compact": 360, "full": 480},
            "margin_start": 0,
            "margin_end": 0,
        },
        "float": {
            "x": 100, "y": 100,
            "sizes": {"compact": {"w": 380, "h": 260}, "full": {"w": 520, "h": 420}},
        },
        "buttons": [
            {"id": "mic", "enabled": True},
            {"id": "notepad", "enabled": True},
            {"id": "downloads", "enabled": True},
            {"id": "browser", "enabled": True},
        ],
        "show_system_buttons": True,
    },
    "plugins": {"dictation": True, "notes": True, "quick_actions": True},
    "notes": {
        "base_file": "Base.txt",
        "note_ext": ".txt",
        "topics": ["ΣΧΟΛΕΙΟ", "PROMPT", "TO-DO", "ΛΟΓΑΡΙΑΣΜΟΣ", "ΥΠΕΝΘΥΜΙΣΗ",
                   "ΔΟΚΙΜΕΣ", "ΠΡΟΓΡΑΜΜΑΤΙΣΜΟΣ", "SNIPPET"],
        "default_topic": "",
        "copy_to_clipboard": True,
        "write_base": True,
        "write_topic": True,
        "clear_after_ok": True,
        "notepad_opens_base": True,
    },
    "quick_actions": {
        "downloads_path": "",
        "browser_exe": "",
        "browser_urls": ["https://www.google.com"],
    },
    "commands": {
        "enabled": True,
        "mode": "auto",
        "threshold": 80,
        "items": [
            {
                "id": "explorer", "enabled": True,
                "phrases": ["εξερεύνηση", "εξερευνητής", "αρχεία"],
                "immediate": True, "confirm": False, "sound": False,
                "args": ["explorer.exe", "{downloads}"]
            },
            {
                "id": "network", "enabled": True,
                "phrases": ["δίκτυο", "browser", "ίντερνετ"],
                "immediate": True, "confirm": False, "sound": False,
                "args": ["{browser}", "https://www.google.com"]
            },
            {
                "id": "notes", "enabled": True,
                "phrases": ["σημειώσεις", "σημειωματάριο"],
                "immediate": True, "confirm": False, "sound": False,
                "args": ["notepad.exe", "{base}"]
            }
        ],
    },
    "speech": {
        "lang": "el",
        "langs": ["el", "en"],
        "providers": ["google", "whisper"],
        "device": "",
        "sample_rate": 16000,
        "silence": {
            "enabled": True,
            "threshold": 500,
            "stop_after_s": 1.5,
            "no_speech_timeout_s": 6.0,
            "max_s": 60.0,
        },
        "google": {"timeout_s": 10},
        "whisper": {"model": "small", "device": "cpu", "compute_type": "int8",
                    "model_dir": "models", "beam_size": 1},
    },
    "autostart": False,
}


def app_root() -> Path:
    """Ρίζα εφαρμογής (portable). Παράκαμψη με TOOLDOCK_HOME."""
    env = os.environ.get("TOOLDOCK_HOME")
    if env:
        return Path(env)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[3]


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
    v3->v4: προστίθενται defaults φωνητικών εντολών, αν δεν υπάρχουν.
    """
    version = from_version if from_version is not None else int(cfg.get("config_version", 1))
    dock = cfg.get("ui", {}).get("dock", {})
    thickness = dock.get("thickness")
    if isinstance(thickness, (int, float)) and not isinstance(thickness, bool):
        dock["thickness"] = {"compact": int(thickness), "full": int(thickness)}
    if version < 3:
        buttons = cfg.setdefault("ui", {}).get("buttons")
        if isinstance(buttons, list) and not any(
                isinstance(button, dict) and button.get("id") == "mic" for button in buttons):
            buttons.insert(0, {"id": "mic", "enabled": True})
    if version < 4:
        commands = cfg.setdefault("commands", {})
        # ΠΡΟΣΟΧΗ: κενή λίστα items είναι σκόπιμη επιλογή και διατηρείται.
        if "items" not in commands:
            commands["items"] = copy.deepcopy(DEFAULTS["commands"]["items"])
    cfg["config_version"] = CONFIG_VERSION
    return cfg


class Config:
    """Φορτώνει/αποθηκεύει το config.json δίπλα στην εφαρμογή."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root else app_root()
        self.path = self.root / "config.json"
        self.data: dict[str, Any] = copy.deepcopy(DEFAULTS)

    def load(self) -> "Config":
        """Πρώτη εκτέλεση: αντιγράφει config.example.json (αν υπάρχει) ή γράφει defaults."""
        if not self.path.exists():
            example = self.root / "config.example.json"
            if example.exists():
                shutil.copyfile(example, self.path)
            else:
                self.save()
        try:
            user = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            # ΠΡΟΣΟΧΗ: χαλασμένο JSON -> αντίγραφο ασφαλείας και επαναφορά defaults
            log.error("Άκυρο config.json (%s). Επαναφορά defaults.", exc)
            self.path.replace(self.path.with_suffix(".json.bad"))
            user = {}
        version = int(user.get("config_version", 1)) if user else CONFIG_VERSION
        self.data = migrate(deep_merge(DEFAULTS, user), from_version=version)
        return self

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, dotted: str, default: Any = None) -> Any:
        current: Any = self.data
        for part in dotted.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def set(self, dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        current = self.data
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value

    @property
    def data_dir(self) -> Path:
        directory = Path(self.get("data_dir", "data"))
        return directory if directory.is_absolute() else self.root / directory
