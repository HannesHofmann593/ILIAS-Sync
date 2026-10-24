import pytest

import courses

# Titel wie in „Meine Kurse und Gruppen“ (crs = Kurs, grp = Gruppe)
ILIAS = [
    ("B.Sc. Wifo_Zeitmanagement [BS] [2. PG] (HWS 2026)", "grp/10"),
    ("Formale Grundlagen der Informatik [V] (HWS 2026)", "crs/11"),
    ("License Information (Student University of Mannheim)", "crs/12"),
    ("Marketing [V] (HWS 2026)", "crs/13"),
    ("Marketing [1. PG]", "grp/14"),
    ("Praktische Informatik I [V] [1. PG] (HWS 2026)", "crs/15"),
    ("Praktische Informatik I [Ü] [1. PG] (HWS 2026)", "grp/16"),
    ("Praktische Informatik I [T] (HWS 2026)", "crs/17"),
    ("Praktische Informatik I Tut Nebenfach Programmierung (HWS 2026)", "crs/18"),
    ("Programmierpraktikum I [V] (HWS 2026)", "crs/19"),
    ("Programmierpraktikum I, Große Übung [Ü] (HWS 2026)", "crs/20"),
    ("IS 201 Wirtschaftsinformatik I: Einführung und Grundlagen [V] (HWS 2026)", "crs/21"),
]


def _entries(items):
    return [{"title": title, "url": f"https://ilias.uni-mannheim.de/goto.php/{path}"} for title, path in items]


def test_suggest_real_course_list():
    settings = courses.suggest(_entries(ILIAS), {})
    names = [settings[title]["name"] for title, _ in ILIAS]
    assert names == [
        "B.Sc. Wifo_Zeitmanagement",
        "Formale Grundlagen der Informatik",
        "License Information (Student University of Mannheim)",
        "Marketing",
        "Marketing/Übungsgruppe",
        "Praktische Informatik I",
        "Praktische Informatik I/Übung",
        "Praktische Informatik I/Tutorium",
        "Praktische Informatik I/Tutorium Nebenfach Programmierung",
        "Programmierpraktikum I",
        "Programmierpraktikum I/Große Übung",
        "Wirtschaftsinformatik I",
    ]
    assert settings["License Information (Student University of Mannheim)"]["sync"] is False


def test_suggest_uses_renamed_folder_of_known_course():
    known = {"Marketing [V] (HWS 2026)": {"name": "Mkt", "sync": True, "url": "crs/13", "group": False}}
    new = courses.suggest(_entries([("Marketing [V] (HWS 2026)", "crs/13"), ("Marketing [Ü] (HWS 2026)", "crs/22")]),
                          known)
    assert new == {"Marketing [Ü] (HWS 2026)": {
        "name": "Mkt/Übung", "sync": True, "url": "https://ilias.uni-mannheim.de/goto.php/crs/22", "group": False,
    }}


def test_suggest_numbers_duplicates_and_keeps_similar_courses_apart():
    new = courses.suggest(_entries([
        ("Praktische Informatik I [V] (HWS 2026)", "crs/1"),
        ("Praktische Informatik II [V] (HWS 2026)", "crs/2"),
        ("Praktische Informatik I [V] (FSS 2027)", "crs/3"),
    ]), {})
    assert [s["name"] for s in new.values()] == [
        "Praktische Informatik I", "Praktische Informatik II", "Praktische Informatik I (2)",
    ]


def test_short_name_removes_code_term_and_subtitle():
    assert courses.short_name("ACC 300 Introduction to Financial Accounting [V] (WT 2026)") == \
        "Introduction to Financial Accounting"
    assert courses.short_name("Kosten/Leistung [V]") == "Kosten-Leistung"


@pytest.mark.parametrize(("typed", "expected"), [
    (" A  B ", "A B"),
    ("Praktische Informatik I / Übung", "Praktische Informatik I/Übung"),
    ("../../etc", "etc"),
    ("/", "Kurs"),
    (".versteckt/x", "versteckt/x"),
])
def test_safe_folder_name(typed, expected):
    assert courses.safe_folder_name(typed) == expected
