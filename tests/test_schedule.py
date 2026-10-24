import pytest

import schedule


def test_parse_times_accepts_common_formats():
    assert schedule.parse_times("18.05, 7  12:30 Uhr; 7:00") == ["07:00", "12:30", "18:05"]


@pytest.mark.parametrize("text", ["", "25:00", "7:60", "morgens"])
def test_parse_times_rejects_invalid(text):
    with pytest.raises(schedule.InvalidTimes):
        schedule.parse_times(text)


def test_configured_times_falls_back_to_old_interval():
    assert schedule.configured_times({"times": ["08:00"]}) == ["08:00"]
    assert schedule.configured_times({"interval_minutes": 60}) == schedule.PRESETS[1][1]
    assert len(schedule.configured_times({})) == 34  # alle 30 Minuten von 6 bis 22:30


def test_job_runs_at_chosen_times_in_own_dev_folder():
    job = schedule.job(["07:00", "18:30"])
    assert job["StartCalendarInterval"] == [{"Hour": 7, "Minute": 0}, {"Hour": 18, "Minute": 30}]
    assert job["ProgramArguments"][-1] == "--scheduled"
    assert job["Label"] == "local.ilias-sync-dev"  # Tests fassen den echten Job nie an
    assert "ILIAS_SYNC_HOME" in job["EnvironmentVariables"]


def test_describe_names_presets():
    assert schedule.describe(schedule.PRESETS[2][1]) == schedule.PRESETS[2][0]
    assert schedule.describe(["06:15"]) == "06:15 Uhr"
