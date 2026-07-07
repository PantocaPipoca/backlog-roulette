"""
actives.py -- manages data/actives.json.

Each active entry tracks one currently-in-progress item:
{
    "category":  "games",
    "wheel":     "my_games.json",
    "item_name": "Elden Ring",
    "spun_at":   "2025-01-15T14:32:00"
}
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


_FILENAME = "actives.json"


def _path(folder: Path) -> Path:
    p = folder / "data"
    p.mkdir(exist_ok=True)
    return p / _FILENAME


def _read(folder: Path) -> list[dict]:
    p = _path(folder)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _write(folder: Path, actives: list[dict]) -> None:
    _path(folder).write_text(
        json.dumps(actives, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_actives(folder: Path) -> list[dict]:
    return _read(folder)


def get_active_for_category(folder: Path, category: str) -> dict | None:
    for entry in _read(folder):
        if entry.get("category") == category:
            return entry
    return None


def get_active_for_wheel(folder: Path, category: str, wheel: str) -> dict | None:
    for entry in _read(folder):
        if entry.get("category") == category and entry.get("wheel") == wheel:
            return entry
    return None


def add_active(folder: Path, category: str, wheel: str, item_name: str) -> dict:
    actives = _read(folder)
    entry = {
        "category":  category,
        "wheel":     wheel,
        "item_name": item_name,
        "spun_at":   datetime.now().isoformat(timespec="seconds"),
    }
    actives.append(entry)
    _write(folder, actives)
    return entry


def remove_active(folder: Path, category: str, wheel: str, item_name: str) -> None:
    actives = _read(folder)
    actives = [
        e for e in actives
        if not (
            e.get("category")  == category
            and e.get("wheel") == wheel
            and e.get("item_name") == item_name
        )
    ]
    _write(folder, actives)