import builtins

import cli
import core
from core import MIRROR_DIR

# So hat die Einrichtung vor dieser Änderung die Kurse benannt
OLD = {
    "Praktische Informatik I [V] [1. PG] (HWS 2026)": ("Praktische Informatik I", "crs/15"),
    "Praktische Informatik I [Ü] [1. PG] (HWS 2026)": ("Praktische Informatik I (2)", "grp/16"),
    "Praktische Informatik I [T] (HWS 2026)": ("Praktische Informatik I (3)", "crs/17"),
    "Programmierpraktikum I [V] (HWS 2026)": ("Programmierpraktikum I", "crs/19"),
    "Programmierpraktikum I, Große Übung [Ü] (HWS 2026)": ("Programmierpraktikum I, Große Übung", "crs/20"),
    "IS 201 Wirtschaftsinformatik I: Einführung und Grundlagen [V] (HWS 2026)": (
        "Wirtschaftsinformatik I: Einführung und Grundl", "crs/21"),
}


def _config(target):
    return {**core.DEFAULT_CONFIG, "target_dir": str(target), "courses": {
        title: {"name": name, "sync": True, "url": f"https://ilias/goto.php/{url}", "group": "grp" in url}
        for title, (name, url) in OLD.items()
    }}


def _file(base, relative):
    (base / relative).parent.mkdir(parents=True, exist_ok=True)
    (base / relative).write_text("x", encoding="utf-8")


def test_apply_suggested_names_moves_downloaded_files(tmp_path, monkeypatch):
    target = tmp_path / "ILIAS"
    config, state = _config(target), core.load_state()
    for base in (MIRROR_DIR, target):
        _file(base, "Praktische Informatik I/Folien.pdf")
        _file(base, "Praktische Informatik I (2)/Blatt 1.pdf")
        _file(base, "Wirtschaftsinformatik I: Einführung und Grundl/Kapitel 1.pdf")
    state["published"] = {"Praktische Informatik I (2)/Blatt 1.pdf": 1.0}
    monkeypatch.setattr(builtins, "input", lambda prompt="": "j")

    cli.apply_suggested_names(config, state)

    names = {settings["name"] for settings in config["courses"].values()}
    assert names == {
        "Praktische Informatik I", "Praktische Informatik I/Übung", "Praktische Informatik I/Tutorium",
        "Programmierpraktikum I", "Programmierpraktikum I/Große Übung", "Wirtschaftsinformatik I",
    }
    for base in (MIRROR_DIR, target):
        assert (base / "Praktische Informatik I/Folien.pdf").exists()
        assert (base / "Praktische Informatik I/Übung/Blatt 1.pdf").exists()
        assert (base / "Wirtschaftsinformatik I/Kapitel 1.pdf").exists()
        assert not (base / "Praktische Informatik I (2)").exists()
    assert state["published"] == {"Praktische Informatik I/Übung/Blatt 1.pdf": 1.0}


def test_rename_course_refuses_own_subfolder_and_taken_names(tmp_path):
    config, state = _config(tmp_path), core.load_state()
    title = "Programmierpraktikum I [V] (HWS 2026)"
    assert not cli.rename_course(config, state, title, "Programmierpraktikum I/Vorlesung")
    assert not cli.rename_course(config, state, title, "Praktische Informatik I")
    assert cli.rename_course(config, state, title, "Prog I / Vorlesung")
    assert config["courses"][title]["name"] == "Prog I/Vorlesung"
