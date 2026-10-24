import os

import core
import sync
from core import MIRROR_DIR


def _mirror_file(relative: str, content: str = "x", mtime: float = 1_700_000_000) -> None:
    path = MIRROR_DIR / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    os.utime(path, (mtime, mtime))


def test_publish_copies_new_files_once(tmp_path):
    config, state = {"target_dir": str(tmp_path)}, core.load_state()
    _mirror_file("Marketing/Folien 1.pdf")
    _mirror_file(".report")  # versteckte Dateien von PFERD nie kopieren
    assert sync.publish(config, state) == [("Marketing/Folien 1.pdf", False)]
    assert (tmp_path / "Marketing/Folien 1.pdf").exists()
    assert not (tmp_path / ".report").exists()
    assert sync.publish(config, state) == []


def test_publish_keeps_old_version_and_respects_deletions(tmp_path):
    config, state = {"target_dir": str(tmp_path)}, core.load_state()
    _mirror_file("Kurs/Blatt.pdf", "alt")
    _mirror_file("Kurs/Gelöscht.pdf")
    sync.publish(config, state)
    (tmp_path / "Kurs/Gelöscht.pdf").unlink()

    _mirror_file("Kurs/Blatt.pdf", "neu", mtime=1_800_000_000)  # auf ILIAS geändert
    copied = sync.publish(config, state)

    assert copied == [("Kurs/Blatt.pdf", True)]
    assert (tmp_path / "Kurs/Blatt.pdf").read_text(encoding="utf-8") == "alt"
    updated = [p.name for p in (tmp_path / "Kurs").iterdir() if "aktualisiert" in p.name]
    assert len(updated) == 1
    assert not (tmp_path / "Kurs/Gelöscht.pdf").exists()


def test_allowed_now_quiet_hours_except_chosen_times():
    assert sync.allowed_now(12, [])
    assert not sync.allowed_now(23, ["07:00"])
    assert not sync.allowed_now(3, ["07:00"])
    assert sync.allowed_now(3, ["03:15"])


def test_scheduled_run_skips_in_quiet_hours(monkeypatch):
    class Night:
        @staticmethod
        def now():
            return Night()

        hour = 2

    monkeypatch.setattr(sync, "datetime", Night)
    monkeypatch.setattr(sync, "run_pferd", lambda *a: (_ for _ in ()).throw(AssertionError("nicht starten")))
    core.save_config({**core.DEFAULT_CONFIG, "uni_id": "mmuster", "target_dir": "/tmp", "times": ["07:00"]})
    sync.run(scheduled=True)


def test_run_reports_new_files(tmp_path, monkeypatch, notifications):
    core.save_config({**core.DEFAULT_CONFIG, "uni_id": "mmuster", "target_dir": str(tmp_path)})
    core.save_state({**core.DEFAULT_STATE, "published": {"Kurs/alt.pdf": 1.0}})

    def fake_pferd(config):
        _mirror_file("Kurs/Neu.pdf")
        return {"added": {"Kurs/Neu.pdf"}, "changed": set(), "entries": [], "new": {}}

    monkeypatch.setattr(sync, "run_pferd", fake_pferd)
    sync.run()
    assert (tmp_path / "Kurs/Neu.pdf").exists()
    assert notifications == [("Neu auf ILIAS: 1 Datei", "Neu")]


def test_run_counts_crawl_failures(tmp_path, monkeypatch, notifications):
    core.save_config({**core.DEFAULT_CONFIG, "uni_id": "mmuster", "target_dir": str(tmp_path)})

    def offline(config):
        raise sync.CrawlFailed("keine Verbindung zu ILIAS", login=False)

    monkeypatch.setattr(sync, "run_pferd", offline)
    sync.run()
    sync.run()
    assert core.load_state()["crawl_failures"] == 2
    assert notifications[-1][0] == "ILIAS nicht erreichbar"


def test_pferd_config_drops_files_folder_also_in_subfolders():
    from pathlib import PurePath

    from PFERD.transformer import Transformer

    config = {**core.DEFAULT_CONFIG, "uni_id": "mmuster", "courses": {
        "A": {"name": "Praktische Informatik I", "sync": True},
        "B": {"name": "Praktische Informatik I/Übung (2)", "sync": True},
    }}
    text = sync.write_pferd_config(config).read_text(encoding="utf-8")
    rules = text.split("transform =\n")[1].split("\n\n")[0]
    transformer = Transformer(rules)

    def moved(path):
        return str(transformer.transform(PurePath(path)))

    assert moved("Praktische Informatik I/Dateien/Folien.pdf") == "Praktische Informatik I/Folien.pdf"
    assert moved("Praktische Informatik I/Übung (2)/Dateien/Blatt.pdf") == "Praktische Informatik I/Übung (2)/Blatt.pdf"
    assert moved("Praktische Informatik I/Übung (2)/Dateien") == "Praktische Informatik I/Übung (2)"
    other = "Praktische Informatik I/Übung (2)/Sonstiges/x.pdf"
    assert moved(other) == other
