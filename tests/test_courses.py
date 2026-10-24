import courses


def test_short_name_removes_code_and_term():
    title = "ACC 300 Introduction to Financial Accounting [V] (WT 2026)"
    assert courses.short_name(title) == "Introduction to Financial Accounting"


def test_suggest_puts_group_below_course_and_avoids_duplicates():
    entries = [
        {"title": "MAN 301 Marketing [Ü] (HWS 2026)", "url": "https://ilias/goto.php/grp/2"},
        {"title": "MAN 301 Marketing [V] (HWS 2026)", "url": "https://ilias/goto.php/crs/1"},
        {"title": "License Information", "url": "https://ilias/goto.php/crs/3"},
    ]
    known = {"Alt": {"name": "Marketing", "sync": True, "url": "", "group": False}}
    new = courses.suggest(entries, known)
    assert new["MAN 301 Marketing [V] (HWS 2026)"]["name"] == "Marketing (2)"
    assert new["MAN 301 Marketing [Ü] (HWS 2026)"]["group"] is True
    assert new["License Information"]["sync"] is False


def test_safe_folder_name_has_no_slash():
    assert courses.safe_folder_name(" A/B  C ") == "A-B C"
