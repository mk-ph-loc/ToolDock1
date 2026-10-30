"""Tests μηχανής φωνητικών εντολών (S3)."""
from pathlib import Path

import pytest

from tooldock.core.commands import CommandEngine
from tooldock.core.config import DEFAULTS, Config, migrate
from tooldock.core.textnorm import normalize

try:
    import rapidfuzz  # noqa: F401
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

requires_rapidfuzz = pytest.mark.skipif(
    not HAS_RAPIDFUZZ, reason="rapidfuzz δεν είναι εγκατεστημένο")


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


def test_normalize_removes_accents_and_case() -> None:
    assert normalize("  ΕΞΕΡΕΎΝΗΣΗ  ") == "εξερευνηση"


@requires_rapidfuzz
def test_match_accepts_accented_phrase() -> None:
    engine = CommandEngine(FakeCfg(DEFAULTS))
    match = engine.match("άνοιξε την εξερεύνηση")
    assert match is not None
    assert match.command["id"] == "explorer"
    assert match.score >= 80


@requires_rapidfuzz
def test_match_below_threshold_returns_none() -> None:
    data = {"commands": {"threshold": 99, "items": DEFAULTS["commands"]["items"]}}
    engine = CommandEngine(FakeCfg(data))
    assert engine.match("τελείως άσχετο κείμενο") is None


@requires_rapidfuzz
def test_execute_uses_argument_list(monkeypatch, tmp_path) -> None:
    calls = []
    monkeypatch.setattr("tooldock.core.commands.subprocess.Popen",
                         lambda args, cwd=None: calls.append((args, cwd)))
    engine = CommandEngine(FakeCfg(DEFAULTS, tmp_path))
    match = engine.match("εξερεύνηση")
    assert match is not None
    assert engine.execute(match) is True
    assert calls[0][0][0] == "explorer.exe"
    assert calls[0][1] == str(tmp_path)


def test_config_v3_migration_adds_commands() -> None:
    old = {"config_version": 3}
    migrated = migrate(old, from_version=3)
    assert migrated["config_version"] == 4
    assert migrated["commands"]["threshold"] == 80
    assert len(migrated["commands"]["items"]) == 3


def test_config_v3_migration_preserves_empty_commands() -> None:
    old = {"config_version": 3, "commands": {"items": []}}
    migrated = migrate(old, from_version=3)
    assert migrated["commands"]["items"] == []


def test_config_load_creates_commands(tmp_path) -> None:
    config = Config(tmp_path).load()
    assert config.get("commands.mode") == "auto"
    assert config.get("commands.threshold") == 80
