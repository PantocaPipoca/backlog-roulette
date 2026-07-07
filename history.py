"""
history.py.

Entry schema:
{
    "item_name": "Elden Ring",
    "category":  "games",
    "wheel":     "my_games.json",
    "event":     "spun | finished | incomplete | dropped",
    "rating":    4,
    "timestamp": "2025-01-15T14:32:00"
}
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from models import Item


_FILENAME = "history.json"


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


def _write(folder: Path, history: list[dict]) -> None:
    _path(folder).write_text(
        json.dumps(history, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def append_event(
    folder: Path,
    item:   Item,
    wheel:  str,
    event:  str,
    rating: int | None = None,
) -> None:
    history = _read(folder)
    entry: dict = {
        "item_name": item.name,
        "category":  item.backlog_type,
        "wheel":     wheel,
        "event":     event,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    if rating is not None:
        entry["rating"] = rating
    history.append(entry)
    _write(folder, history)


def load_history(folder: Path) -> list[dict]:
    return _read(folder)