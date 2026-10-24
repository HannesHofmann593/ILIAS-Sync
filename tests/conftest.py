"""Testumgebung: eigener Datenordner, Schlüsselbund nur im Speicher, keine Mitteilungen.

core.py liest ILIAS_SYNC_HOME beim Import, deshalb wird alles gesetzt, bevor ein Test
die App-Module importiert.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import keyring
import keyring.backend
import keyring.errors
import pytest

ROOT = Path(__file__).resolve().parent.parent
HOME = Path(tempfile.mkdtemp(prefix="ilias-sync-test-"))
os.environ["ILIAS_SYNC_HOME"] = str(HOME)
sys.path.insert(0, str(ROOT / "app"))


class MemoryKeyring(keyring.backend.KeyringBackend):
    priority = 1

    def __init__(self):
        super().__init__()
        self.store: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self.store.get((service, username))

    def set_password(self, service, username, password):
        self.store[(service, username)] = password

    def delete_password(self, service, username):
        if self.store.pop((service, username), None) is None:
            raise keyring.errors.PasswordDeleteError(username)


keyring.set_keyring(MemoryKeyring())


@pytest.fixture(autouse=True)
def clean_home():
    """Jeder Test beginnt mit leerem Datenordner."""
    for child in HOME.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    yield HOME


@pytest.fixture
def notifications(monkeypatch):
    """Fängt Mac-Mitteilungen ab, statt osascript aufzurufen."""
    import notify
    import sync

    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(notify, "notify", lambda title, message: sent.append((title, message)))
    monkeypatch.setattr(sync, "notify", lambda title, message: sent.append((title, message)))
    monkeypatch.setattr(subprocess, "run", _no_subprocess)
    return sent


def _no_subprocess(*args, **kwargs):
    raise AssertionError(f"Test hat ein Programm gestartet: {args}")
