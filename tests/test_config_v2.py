import json

from tooldock.core.config import Config, migrate


def test_migrate_int_thickness():
    out = migrate({"ui": {"dock": {"thickness": 500}}})
    assert out["ui"]["dock"]["thickness"] == {"compact": 500, "full": 500}


def test_old_config_file_loads(tmp_path):
    old = {"ui": {"dock": {"state": "right", "thickness": 420}, "float": {"x": 5, "y": 6, "w": 300, "h": 200}}}
    (tmp_path / "config.json").write_text(json.dumps(old), encoding="utf-8")
    c = Config(tmp_path).load()
    assert c.get("ui.dock.thickness.full") == 420
    assert c.get("ui.screen") == "auto"
    assert c.get("ui.float.x") == 5
