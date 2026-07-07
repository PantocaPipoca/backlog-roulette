"""
settings.py
Load, save, and validate app settings from data/settings.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from constants import DEFAULT_SETTINGS


def _data_dir(folder: Path) -> Path:
    """
    Args:
        folder (Path): The base folder of the app.
    Returns:
        Path: Path to data folder, creating it if it doesn't exist.
    """

    p = folder / "data"
    p.mkdir(exist_ok=True) # Creates the folder if doessnt exist
    return p


def load_settings(folder: Path) -> dict:
    """
    Loads the settings from data/settings.json
    If does't exist yet created with DEFAULT_SETTINGS.

    Args:
        folder (Path): The base folder of the app.

    Returns:
        dict: The loaded settings with no more settings than specified in DEFAULT_SETTINGS.
    """

    path = _data_dir(folder) / "settings.json"
    if not path.exists():
        save_settings(folder, DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        merged = dict(DEFAULT_SETTINGS)
        merged.update({key: value for key, value in data.items() if key in DEFAULT_SETTINGS})
        return merged
    except json.JSONDecodeError:
        return dict(DEFAULT_SETTINGS)


def save_settings(folder: Path, settings: dict) -> None:
    """
    Saves the settings to data/settings.json, creating the file if it doesn't exist.
    Args:
        folder (Path): The base folder of the app.
        settings (dict): The settings to save.
    """

    path = _data_dir(folder) / "settings.json"
    existing: dict = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    existing.update(settings)
    path.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_last_spinned(folder: Path) -> str | None:
    """
    Gets the last spinned wheel from settings.

    Args:
        folder (Path): The base folder of the app.

    Returns:
        str | None: The last spinned wheel, or None if not found.
    """

    path = _data_dir(folder) / "settings.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("_last_spinned")
    except Exception:
        return None


def set_last_spinned(folder: Path, wheel: str) -> None:
    """
    Sets the last spinned wheel in settings.

    Args:
        folder (Path): The base folder of the app.
        wheel (str): The wheel to set as the last spinned.
    """

    path = _data_dir(folder) / "settings.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    data["_last_spinned"] = wheel
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")