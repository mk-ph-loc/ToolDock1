from datetime import datetime

from tooldock.core.config import Config
from tooldock.core.storage import Storage, format_entry, safe_topic_name

NOW = datetime(2026, 10, 28, 13, 41)


def test_base_entry_format():
    s = format_entry("Γεια", "PROMPT", NOW, in_base=True)
    assert s == "──────── 2026-10-28 13:41 · PROMPT ────────\nΓεια\n[ΘΕΜΑ: PROMPT · 2026-10-28 13:41]\n\n"


def test_topic_entry_format_date_only():
    s = format_entry("Γεια", "PROMPT", NOW, in_base=False)
    assert s.startswith("──────── 2026-10-28 ────────\n")
    assert "[ΘΕΜΑ: PROMPT · 2026-10-28 13:41]" in s


def test_no_topic():
    s = format_entry("x", "", NOW, in_base=True)
    assert s.splitlines()[0] == "──────── 2026-10-28 13:41 ────────"
    assert s.splitlines()[2] == "[2026-10-28 13:41]"


def test_first_run_files(tmp_path):
    cfg = Config(tmp_path).load()
    st = Storage(cfg)
    st.ensure_files()
    assert st.base_path.exists()
    for t in cfg.get("notes.topics"):
        assert st.topic_path(t).exists()
    assert (tmp_path / "data" / "logs").is_dir()


def test_ensure_keeps_existing(tmp_path):
    cfg = Config(tmp_path).load()
    st = Storage(cfg)
    st.ensure_files()
    st.base_path.write_text("keep", encoding="utf-8")
    st.ensure_files()
    assert st.base_path.read_text(encoding="utf-8") == "keep"


def test_save_note_writes_both_and_appends(tmp_path):
    cfg = Config(tmp_path).load()
    st = Storage(cfg)
    st.ensure_files()
    assert len(st.save_note("α", "PROMPT", NOW)) == 2
    st.save_note("β", "PROMPT", NOW)
    txt = st.topic_path("PROMPT").read_text(encoding="utf-8")
    assert txt.count("[ΘΕΜΑ: PROMPT") == 2 and "α" in txt and "β" in txt
    assert "· PROMPT ────────" in st.base_path.read_text(encoding="utf-8")


def test_save_note_no_topic_only_base(tmp_path):
    cfg = Config(tmp_path).load()
    st = Storage(cfg)
    st.ensure_files()
    assert st.save_note("α", "", NOW) == [st.base_path]


def test_empty_note_ignored(tmp_path):
    st = Storage(Config(tmp_path).load())
    assert st.save_note("   ", "PROMPT") == []


def test_safe_topic_name():
    assert safe_topic_name('A/B:C?') == "A_B_C_"
