"""Tests μηχανής φωνητικών εντολών (S3)."""
import json
from pathlib import Path

import pytest

from tooldock.core.commands import CommandEngine
from tooldock.core.config import DEFAULTS, Config
from tooldock.core.textnorm import normalize


class FakeCfg:
    """Ελάχιστο cfg για tests της μηχανής εντολών."""

    def __init__(self, data: dict, root: Path | None = None) -> None:
        self.data = data
        self.root = root or Path(".")

    def get(self, dotted: str, default=None):
        current = self.data
        for part in dotted.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current


needs_fuzz = pytest.mark.skipif(
    not CommandEngine(FakeCfg({})).available(),
    reason="rapidfuzz δεν είναι εγκατεστημένο (requirements-commands.txt)")


def test_normalize_removes_accents_and_case() -> None:
    assert normalize("  ΕΞΕΡΕΥΝΗΣΗ  ") == "εξερευνηση"


@needs_fuzz
def test_match_accepts_accented_phrase() -> None:
    engine = CommandEngine(FakeCfg(DEFAULTS))
    match = engine.match("άνοιξε την εξερεύνηση")
    assert match is not None
    assert match.command["id"] == "explorer"
    assert match.score >= 80


@needs_fuzz
def test_match_below_threshold_returns_none() -> None:
    data = {"commands": {"threshold": 99, "items": DEFAULTS["commands"]["items"]}}
    engine = CommandEngine(FakeCfg(data))
    assert engine.match("τελείως άσχετο κείμενο") is None


def test_config_v3_without_commands_gets_defaults(tmp_path) -> None:
    (tmp_path / "config.json").write_text(json.dumps({"config_version": 3}), encoding="utf-8")
    config = Config(tmp_path).load()
    assert config.get("config_version") == 4
    assert config.get("commands.threshold") == 80
    assert len(config.get("commands.items")) == 3


def test_empty_user_commands_are_preserved(tmp_path) -> None:
    user = {"config_version": 3, "commands": {"items": []}}
    (tmp_path / "config.json").write_text(json.dumps(user), encoding="utf-8")
    config = Config(tmp_path).load()
    assert config.get("commands.items") == []


def test_config_load_creates_commands(tmp_path) -> None:
    (tmp_path / "config.json").write_text(json.dumps({"config_version": 3}), encoding="utf-8")
    config = Config(tmp_path).load()
    assert config.get("config_version") == 4
    assert config.get("commands.mode") == "compact"
    assert config.get("commands.threshold") == 80
