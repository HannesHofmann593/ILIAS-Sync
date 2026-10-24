"""Automatischer Abgleich über launchd: zu den eingestellten Uhrzeiten und beim Anmelden.

Die Uhrzeiten stehen in config["times"] (z. B. ["07:00", "12:30", "18:00"]). Verpasst der
Mac eine Uhrzeit im Ruhezustand, holt launchd den Abgleich nach dem Aufwachen nach.
"""

import os
import plistlib
import re
import subprocess
from pathlib import Path

import core
from core import CODE_DIR, LOG_FILE, PYTHON

# Mit ILIAS_SYNC_HOME (Entwicklung, Tests) ein eigener Job, damit der echte unberührt bleibt
DEV = bool(os.environ.get("ILIAS_SYNC_HOME"))
LABEL = "local.ilias-sync-dev" if DEV else "local.ilias-sync"
PLIST = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
DOMAIN = f"gui/{os.getuid()}"

# Vorschläge im Einrichtungsassistenten: (Bezeichnung, Uhrzeiten)
PRESETS = [
    ("alle 30 Minuten von 6 bis 23 Uhr", [f"{hour:02d}:{minute:02d}" for hour in range(6, 23) for minute in (0, 30)]),
    ("stündlich von 6 bis 23 Uhr", [f"{hour:02d}:00" for hour in range(6, 23)]),
    ("dreimal täglich (7, 13 und 19 Uhr)", ["07:00", "13:00", "19:00"]),
]


class InvalidTimes(ValueError):
    pass


def parse_times(text: str) -> list[str]:
    """ "7, 12:30 18.05" -> ["07:00", "12:30", "18:05"], sortiert und ohne Doppelte."""
    times = set()
    for part in re.split(r"[\s,;]+", text.strip()):
        if not part or part.lower() == "uhr":
            continue
        match = re.fullmatch(r"(\d{1,2})(?:[:.](\d{2}))?", part)
        hour, minute = (int(match[1]), int(match[2] or 0)) if match else (-1, -1)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise InvalidTimes(f"„{part}“ ist keine Uhrzeit (Beispiel: 7:00 oder 18:30)")
        times.add(f"{hour:02d}:{minute:02d}")
    if not times:
        raise InvalidTimes("Bitte mindestens eine Uhrzeit angeben")
    return sorted(times)


def configured_times(config: dict) -> list[str]:
    """Uhrzeiten aus den Einstellungen; ältere Einstellungen kennen nur interval_minutes."""
    if config.get("times"):
        return config["times"]
    return PRESETS[0][1] if config.get("interval_minutes", 30) == 30 else PRESETS[1][1]


def describe(times: list[str]) -> str:
    for label, preset in PRESETS:
        if times == preset:
            return label
    return ", ".join(times) + " Uhr"


def job(times: list[str]) -> dict:
    """Inhalt der launchd-Datei für diese Uhrzeiten."""
    content = {
        "Label": LABEL,
        "ProgramArguments": [str(PYTHON), str(CODE_DIR / "sync.py"), "--scheduled"],
        "StartCalendarInterval": [
            {"Hour": int(time[:2]), "Minute": int(time[3:])} for time in times
        ],
        "RunAtLoad": True,
        "ProcessType": "Background",
        "StandardOutPath": str(LOG_FILE),
        "StandardErrorPath": str(LOG_FILE),
    }
    if DEV:  # launchd startet mit leerer Umgebung, der eigene Datenordner muss mit
        content["EnvironmentVariables"] = {"ILIAS_SYNC_HOME": str(core.APP_DIR), "ILIAS_SYNC_PYTHON": str(PYTHON)}
    return content


def _launchctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["launchctl", *args], capture_output=True, text=True, check=False)


def is_active() -> bool:
    return _launchctl("print", f"{DOMAIN}/{LABEL}").returncode == 0


def start(times: list[str]) -> None:
    """Schreibt den Job neu und aktiviert ihn (bleibt über Neustarts aktiv). Gleicht sofort einmal ab."""
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PLIST, "wb") as file:
        plistlib.dump(job(times), file)
    _launchctl("enable", f"{DOMAIN}/{LABEL}")
    _launchctl("bootout", f"{DOMAIN}/{LABEL}")
    _launchctl("bootstrap", DOMAIN, str(PLIST))


def stop() -> None:
    """Hält den Abgleich an; bleibt auch nach einem Neustart aus."""
    _launchctl("bootout", f"{DOMAIN}/{LABEL}")
    _launchctl("disable", f"{DOMAIN}/{LABEL}")


def remove() -> None:
    _launchctl("bootout", f"{DOMAIN}/{LABEL}")
    _launchctl("enable", f"{DOMAIN}/{LABEL}")  # ein früheres "stop" vergessen
    PLIST.unlink(missing_ok=True)
