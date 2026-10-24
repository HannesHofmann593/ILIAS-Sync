"""Kurse aus "Meine Kurse und Gruppen": kurze Ordnernamen vorschlagen.

Wird vom Einrichtungsassistenten und von pferd_runner.py (für neu auftauchende
Kurse während eines Abgleichs) gleich verwendet, damit die Namen übereinstimmen.

Übungen, Tutorien und Übungsgruppen landen als Unterordner ihres Kurses:
"Praktische Informatik I [Ü] (HWS 2026)" -> "Praktische Informatik I/Übung".
"""

import re

# Kein Lehrinhalt, standardmäßig nicht synchronisiert
EXCLUDED_BY_DEFAULT = re.compile(r"^License Information", re.IGNORECASE)
# Veranstaltungsart in eckigen Klammern -> Unterordner; [V] (Vorlesung) ist der Kurs selbst
KINDS = {"Ü": "Übung", "T": "Tutorium"}
SEPARATORS = " ,:-–"


def short_name(title: str) -> str:
    """"ACC 300 Introduction to Financial Accounting [V] (WT 2026)" -> "Introduction to Financial Accounting"."""
    name = re.sub(r"\s*\[[^\]]*\]", "", title)  # [V], [1. PG]
    name = re.sub(r"\s*\((?:HWS|FSS|HS|FS|WS|SS|WT|ST)\s*\d{2,4}\)", "", name)  # (HWS 2026)
    name = re.sub(r"^[A-Z]{2,5} ?\d{3}[A-Z]?\s+", "", name)  # ACC 300, MAN 301, IS 201
    name = re.sub(r"^(.{3,}?):\s.*$", r"\1", name)  # "Wirtschaftsinformatik I: Einführung …"
    return name.strip(SEPARATORS).replace("/", "-") or title


def kind(title: str) -> str | None:
    """Übung oder Tutorium laut Markierung im Titel, sonst None."""
    for mark in re.findall(r"\[([^\]]*)\]", title):
        if mark.strip() in KINDS:
            return KINDS[mark.strip()]
    return None


def is_group(url: str) -> bool:
    return "/grp/" in url or "grp_" in url


def safe_folder_name(name: str) -> str:
    """Eigener Ordnername: "/" legt einen Unterordner an; leere Teile, "." und ".." fallen weg."""
    parts = [re.sub(r"\s+", " ", part).strip().lstrip(".").strip() for part in name.split("/")]
    return "/".join(part for part in parts if part) or "Kurs"


def _sub_folder(title: str, url: str, main_names: set[str]) -> tuple[str, str] | None:
    """(Kurs, Unterordner), falls der Eintrag zu einem anderen Kurs gehört."""
    name = short_name(title)
    # "Programmierpraktikum I, Große Übung", "Praktische Informatik I Tut Nebenfach"
    for main in sorted(main_names, key=len, reverse=True):
        if name != main and name.startswith(main) and name[len(main)] in SEPARATORS:
            rest = name[len(main):].strip(SEPARATORS)
            return main, re.sub(r"^Tut\b\.?", "Tutorium", rest)
    if kind(title):
        return name, kind(title)
    if is_group(url) and name in main_names:
        return name, "Übungsgruppe"
    return None


def suggest(entries: list[dict], known: dict[str, dict]) -> dict[str, dict]:
    """Einstellungen für bisher unbekannte Kurse und Gruppen.

    entries: [{"title": ..., "url": ...}] von der ILIAS-Übersicht.
    known: bereits bekannte Kurse (ILIAS-Titel -> Einstellungen), deren Namen belegt sind.
    """
    taken = {settings["name"] for settings in known.values()}
    # Kurzname -> Ordnername der Hauptkurse (Vorlesungen), unter denen Unterordner landen
    folders = {
        short_name(title): settings["name"]
        for title, settings in known.items()
        if "/" not in settings["name"] and _sub_folder(title, settings.get("url", ""), set()) is None
    }
    main_names = set(folders) | {
        short_name(e["title"]) for e in entries if not kind(e["title"]) and not is_group(e["url"])
    }
    parts = {e["title"]: _sub_folder(e["title"], e["url"], main_names) for e in entries}

    new: dict[str, dict] = {}
    for entry in sorted(entries, key=lambda e: parts[e["title"]] is not None):  # erst Hauptkurse
        title, url = entry["title"], entry["url"]
        if title in known or title in new:
            continue
        if parts[title] is None:
            name = short_name(title)
        else:
            main, sub = parts[title]
            name = f"{folders.get(main, main)}/{sub}"
        candidate, number = name, 2
        while candidate in taken:
            candidate, number = f"{name} ({number})", number + 1
        taken.add(candidate)
        if parts[title] is None:
            folders.setdefault(short_name(title), candidate)
        new[title] = {
            "name": candidate,
            "sync": not EXCLUDED_BY_DEFAULT.search(title),
            "url": url,
            "group": is_group(url),
        }
    return new
