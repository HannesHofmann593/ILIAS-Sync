# ILIAS-Sync

Lädt neue Dateien aus deinen ILIAS-Kursen der Uni Mannheim **zu Uhrzeiten, die du festlegst,**
automatisch auf deinen Mac und sortiert sie je Kurs in einen Ordner deiner Wahl.

- Nur neue und auf ILIAS geänderte Dateien werden geladen.
- Im Zielordner wird nie etwas überschrieben oder gelöscht. Eine geänderte Datei kommt als
  „… (aktualisiert TT.MM.)“ dazu, und was du dort löschst, wird nicht erneut kopiert.
- Das Passwort liegt nur im macOS-Schlüsselbund und geht nur an `idp.uni-mannheim.de`.
- Mac-Mitteilung bei neuen Dateien, neuen Kursen und Anmeldeproblemen.

Läuft nur auf macOS. Den Download übernimmt [PFERD](https://github.com/Garmelon/PFERD),
angepasst an das Mannheimer ILIAS.

## Installation

```bash
bash install.sh          # oder Doppelklick auf „Installieren.command“
```

Der Installer lädt eine feste, per Prüfsumme kontrollierte Python- und PFERD-Version nach
`~/Library/Application Support/ILIAS-Sync`, legt den Befehl `ilias-sync` an und startet die
Einrichtung (ca. 5 Minuten):

1. Uni-ID und Passwort (die Anmeldung wird gleich geprüft)
2. Kurse auswählen, Ordnernamen anpassen
3. Zielordner (z. B. iCloud Drive › ILIAS)
4. **Zeitplan**: alle 30 Minuten, stündlich, dreimal täglich oder eigene Uhrzeiten (`7:00, 12:30, 18:00`)

Danach lädt der erste Abgleich alles herunter, und ab dann läuft er automatisch.

Hast du Code im Repo geändert, bringt ein erneutes `bash install.sh` die neue Fassung auf den
Mac. Einstellungen und Zeitplan bleiben dabei erhalten.

## Bedienung

| Befehl | Wirkung |
|---|---|
| `ilias-sync` | Übersicht und Menü |
| `ilias-sync jetzt` | sofort abgleichen |
| `ilias-sync zeiten` | Uhrzeiten des automatischen Abgleichs ändern |
| `ilias-sync kurse` | Kurse an-/abwählen, umbenennen |
| `ilias-sync ordner` | Zielordner ändern |
| `ilias-sync zugang` | Uni-ID oder Passwort ändern |
| `ilias-sync stop` / `start` | automatischen Abgleich anhalten / fortsetzen |
| `ilias-sync log` | letzte Einträge im Protokoll |
| `ilias-sync deinstallieren` | alles entfernen (deine Dateien bleiben) |

**Zum Zeitplan:** Ist der Mac zu einer Uhrzeit im Ruhezustand, holt macOS (launchd) den Abgleich
nach dem Aufwachen nach; zusätzlich läuft einer beim Anmelden. Solche nachgeholten Abgleiche
lässt das Programm zwischen 23 und 6 Uhr aus, außer du hast selbst eine Uhrzeit in diesem
Zeitraum gewählt.

## Aufbau

```
app/
  cli.py            Befehl „ilias-sync“: Einrichtung, Menü, Einstellungen
  sync.py           ein Abgleich: PFERD → lokaler Spiegel → Zielordner, Mitteilungen
  pferd_runner.py   startet PFERD mit den Anpassungen für die Uni Mannheim (SAML-Login, Kursauswahl)
  schedule.py       Zeitplan als launchd-Job (~/Library/LaunchAgents/local.ilias-sync.plist)
  courses.py        kurze Ordnernamen aus ILIAS-Kurstiteln
  core.py           Pfade, Einstellungen (config.json), Zustand (state.json), Protokoll
  notify.py         Mac-Mitteilungen
  requirements.lock Abhängigkeiten mit Prüfsummen für den Installer
install.sh          Installation und Update
tests/              pytest, ohne Netz und ohne echte Zugangsdaten
```

Daten auf dem Mac:

- `~/Library/Application Support/ILIAS-Sync/`: Programm, `config.json`, `state.json` und `Spiegel/`.
  PFERD lädt in diesen lokalen Spiegel, in den Zielordner wird nur kopiert. So funktionieren auch
  iCloud-Ordner, deren Dateien „nur online“ liegen.
- `~/Library/Logs/ILIAS-Sync.log`: Protokoll; die PFERD-Ausgabe des letzten Laufs liegt in `ILIAS-Sync-pferd.log`.

## Entwickeln

Voraussetzung ist [uv](https://docs.astral.sh/uv/) (`brew install uv`; nach der Installation
liegt es auch unter `~/Library/Application\ Support/ILIAS-Sync/bin/uv`).

```bash
uv sync                      # .venv mit Python 3.13, PFERD, pytest, ruff
uv run pytest                # Tests
uv run ruff check .          # Lint
```

Ausprobieren, ohne die echte Installation anzufassen: Mit `ILIAS_SYNC_HOME` nutzt das Programm
einen eigenen Datenordner und einen eigenen launchd-Job (`local.ilias-sync-dev`):

```bash
export ILIAS_SYNC_HOME="$PWD/dev-home" ILIAS_SYNC_PYTHON="$PWD/.venv/bin/python"
uv run python app/cli.py einrichten
uv run python app/cli.py jetzt
uv run python app/cli.py stop     # Dev-Job wieder anhalten
```

**Ideen zum Ausbauen:** Telegram-Nachricht bei neuen Dateien, Videos laden (`videos = yes` in
`write_pferd_config`), Zusammenfassungen per KI, eine Menüleisten-App. Im Projekt ILIAS-Lerner
gibt es dafür schon fertige Module (`telegram_bot.py`, `goodnotes.py`, `notion_todo.py`).
