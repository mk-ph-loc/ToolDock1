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
CONFIG_VERSION = 3

DEFAULTS: dict[str, Any] = {
    "config_version": CONFIG_VERSION,
    "data_dir": "data",
    "ui": {
        "mode": "compact",            # buttons | compact | full
        "always_on_top": True,
        "start_hidden": False,
        "screen": "auto",             # auto (όπου βρίσκεται) | 0 | 1 | ... (αριθμός οθόνης)
        "dock": {
            "state": "float",         # float | left | right | top | bottom
            # πάχος ανά mode (πλάτος αν left/right, ύψος αν top/bottom)· το buttons προσαρμόζεται μόνο του
            "thickness": {"compact": 360, "full": 480},
            "margin_start": 0,        # απόσταση από την αρχή της πλευράς (πάνω/αριστερά)
            "margin_end": 0,          # απόσταση από το τέλος της πλευράς (κάτω/δεξιά)
        },
        "float": {                    # το buttons προσαρμόζεται μόνο του στα κουμπιά
            "x": 100, "y": 100,
            "sizes": {"compact": {"w": 380, "h": 260}, "full": {"w": 520, "h": 420}},
        },
        "buttons": [                  # σειρά + on/off ανά κουμπί της λωρίδας
            {"id": "mic", "enabled": True},
            {"id": "notepad", "enabled": True},
            {"id": "downloads", "enabled": True},
            {"id": "browser", "enabled": True},
        ],
        "show_system_buttons": True,  # 📌 mode ⚙
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
        "downloads_path": "",         # κενό = φάκελος Downloads του χρήστη
        "browser_exe": "",            # κενό = προεπιλεγμένος browser
        "browser_urls": ["https://www.google.com"],
    },
    "speech": {
        "lang": "el",                 # τρέχουσα γλώσσα υπαγόρευσης
        "langs": ["el", "en"],        # γλώσσες για το κουμπί εναλλαγής (κωδικοί στο speech/base.py)
        "providers": ["google", "whisper"],  # σειρά προτεραιότητας· αν αποτύχει ο ένας δοκιμάζεται ο επόμενος
        "device": "",                 # όνομα μικροφώνου· κενό = προεπιλεγμένο των Windows
        "sample_rate": 16000,
        "silence": {
            "enabled": True,          # αυτόματο στοπ σε σιωπή (αλλιώς μόνο χειροκίνητο)
            "threshold": 500,         # RMS int16 — ανέβασέ το αν ο χώρος έχει θόρυβο
            "stop_after_s": 1.5,      # σιωπή μετά την ομιλία
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
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def migrate(cfg: dict, from_version: int | None = None) -> dict:
    """Μετατροπές παλιών config.

    v1->v2: πάχος dock ως αριθμός γίνεται dict ανά mode.
    v2->v3: προστίθεται το κουμπί «mic» στη λωρίδα (μία φορά, στην αρχή).
    from_version: η έκδοση του αρχείου του χρήστη ΠΡΙΝ τη συγχώνευση με τα defaults.
    """
    ver = from_version if from_version is not None else int(cfg.get("config_version", 1))
    dock = cfg.get("ui", {}).get("dock", {})
    t = dock.get("thickness")
    if isinstance(t, (int, float)) and not isinstance(t, bool):
        dock["thickness"] = {"compact": int(t), "full": int(t)}
    if ver < 3:
        btns = cfg.setdefault("ui", {}).get("buttons")
        if isinstance(btns, list) and not any(isinstance(b, dict) and b.get("id") == "mic" for b in btns):
            btns.insert(0, {"id": "mic", "enabled": True})
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
        ver = int(user.get("config_version", 1)) if user else CONFIG_VERSION
        self.data = migrate(deep_merge(DEFAULTS, user), from_version=ver)
        return self

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, dotted: str, default: Any = None) -> Any:
        cur: Any = self.data
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    def set(self, dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        cur = self.data
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = value

    @property
    def data_dir(self) -> Path:
        d = Path(self.get("data_dir", "data"))
        return d if d.is_absolute() else self.root / d
