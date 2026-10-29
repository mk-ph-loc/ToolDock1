import json

from tooldock.core.config import DEFAULTS, Config, deep_merge


def test_first_run_creates_defaults(tmp_path):
    c = Config(tmp_path).load()
    assert (tmp_path / "config.json").exists()
    assert c.get("ui.dock.state") == "float"
    assert c.get("ui.always_on_top") is True


def test_user_override_merge(tmp_path):
    (tmp_path / "config.json").write_text(json.dumps({"ui": {"dock": {"state": "right"}}}), encoding="utf-8")
    c = Config(tmp_path).load()
    assert c.get("ui.dock.state") == "right"
    assert c.get("ui.dock.thickness") == DEFAULTS["ui"]["dock"]["thickness"]


def test_bad_json_recovers(tmp_path):
    (tmp_path / "config.json").write_text("{oops", encoding="utf-8")
    c = Config(tmp_path).load()
    assert c.get("ui.mode") == "compact"
    assert (tmp_path / "config.json.bad").exists()


def test_set_get_save_roundtrip(tmp_path):
    c = Config(tmp_path).load()
    c.set("ui.dock.thickness", 500)
    c.save()
    assert Config(tmp_path).load().get("ui.dock.thickness") == 500


def test_example_file_used(tmp_path):
    (tmp_path / "config.example.json").write_text(json.dumps({"ui": {"mode": "full"}}), encoding="utf-8")
    assert Config(tmp_path).load().get("ui.mode") == "full"


def test_deep_merge_lists_replace():
    assert deep_merge({"a": [1, 2]}, {"a": [3]}) == {"a": [3]}


def test_data_dir_relative(tmp_path):
    assert Config(tmp_path).load().data_dir == tmp_path / "data"
