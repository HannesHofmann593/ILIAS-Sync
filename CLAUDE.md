# CLAUDE.md – Projektregeln

Kommandozeilen-Werkzeug für macOS: lädt neue Dateien aus ILIAS (Uni Mannheim) über PFERD zu
eingestellten Uhrzeiten (launchd) in einen Zielordner. Aufbau und Befehle: siehe `README.md`.

## Code-Regeln

- Python 3.13. Die Laufzeit-Abhängigkeiten stehen an zwei Stellen, die gleich bleiben müssen:
  `app/requirements.lock` (mit Prüfsummen, für den Installer) und `constraint-dependencies`
  in `pyproject.toml` (für `uv.lock`, also Entwicklung und Tests). Nach einer Änderung:
  `uv lock`, dann `uv export --no-dev --no-emit-project --format requirements-txt > app/requirements.lock`.
- `pferd` ist fest auf eine Version gepinnt, weil `pferd_runner.py` Interna patcht. Nach einem
  Update den echten Login einmal von Hand testen.
- Die Module in `app/` importieren sich gegenseitig über `sys.path` (kein Paket), zum Beispiel `import core`.
- Secrets (Uni-Passwort, Tokens) nur über `keyring`. Nie in Dateien, Logs oder Commits.
- Das Passwort darf nur an `https://idp.uni-mannheim.de` gehen (`pferd_runner.py`, `_post_only_to_uni_login`).
- Im Zielordner nie überschreiben oder löschen (`sync.publish`).
- Dateien immer mit `encoding="utf-8"` lesen und schreiben. Protokoll über `core.log()`, nicht `print`
  (Ausnahme: Ausgaben der CLI).
- Bezeichner Englisch, Kommentare und Texte für Nutzer Deutsch.

## Tests

- Vor jedem Commit `uv run pytest` und `uv run ruff check .` ausführen (läuft auch in der CI).
- Tests nutzen den Datenordner aus `tests/conftest.py` (`ILIAS_SYNC_HOME`) und den Schlüsselbund
  im Speicher. Nie echte Zugangsdaten, kein Netz, kein echter launchd-Job. PFERD und Mitteilungen
  per `monkeypatch` ersetzen.
- Neue Funktionen bekommen mindestens einen Test.

## Git

- Nicht direkt auf `main` arbeiten: ein Branch pro Aufgabe, dann ein Pull Request.
