from tooldock.core.config import CONFIG_VERSION, DEFAULTS, Config, migrate


def test_defaults_have_speech_and_mic():
    assert CONFIG_VERSION == 4
    assert DEFAULTS["plugins"]["dictation"] is True
    assert DEFAULTS["ui"]["buttons"][0]["id"] == "mic"
    assert DEFAULTS["speech"]["providers"] == ["google", "whisper"]


def test_migrate_adds_mic_once():
    cfg = {"config_version": 2, "ui": {"buttons": [{"id": "notepad", "enabled": True}]}}
    out = migrate(cfg)
    assert out["ui"]["buttons"][0] == {"id": "mic", "enabled": True}
    assert out["config_version"] == 4
    again = migrate({"config_version": 3, "ui": {"buttons": [{"id": "x"}]}})
    assert [b["id"] for b in again["ui"]["buttons"]] == ["x"]
    assert again["config_version"] == 4


def test_migrate_preserves_empty_commands():
    """Κενή λίστα εντολών είναι σκόπιμη επιλογή και δεν αντικαθίσταται."""
    cfg = {"config_version": 3, "commands": {"items": []}}
    out = migrate(cfg, from_version=3)
    assert out["commands"]["items"] == []
    assert out["config_version"] == 4


def test_load_old_file_gets_mic_without_duplicates(tmp_path):
    (tmp_path / "config.json").write_text(
        '{"ui": {"buttons": [{"id": "notepad", "enabled": true}]}}', encoding="utf-8")
    c = Config(tmp_path).load()
    ids = [b["id"] for b in c.get("ui.buttons")]
    assert ids == ["mic", "notepad"]
    assert c.get("speech.whisper.model") == "small"
    assert c.get("plugins.dictation") is True
