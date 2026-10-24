"""Mitteilungen auf dem Mac."""

import subprocess
import time

from core import APP_DIR


def notify(title: str, message: str) -> None:
    script = ["on run argv", "display notification (item 2 of argv) with title (item 1 of argv)", "end run"]
    args = [part for line in script for part in ("-e", line)]
    subprocess.run(["osascript", *args, title, message], check=False, capture_output=True)


def notify_once_a_day(key: str, title: str, message: str) -> None:
    marker = APP_DIR / f".meldung-{key}"
    if marker.exists() and time.time() - marker.stat().st_mtime < 24 * 3600:
        return
    notify(title, message)
    marker.touch()


def clear_once_a_day(key: str) -> None:
    (APP_DIR / f".meldung-{key}").unlink(missing_ok=True)
