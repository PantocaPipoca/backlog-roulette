"""
roulette.py -- loads a backlog JSON, exposes picking / filtering / saving logic.
No UI code lives here.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from constants import BACKLOG_TYPES, DEFAULT_TIERS, _Back
from models import Item


class Roulette:
    def __init__(self, path: Path) -> None:
        self.path  = path
        self.label = path.stem.replace("_", " ").upper()
        self._load()

# ----------------------------------- loading -----------------------------------

    def _load(self) -> None:
        try:
            text = self.path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {self.path}")

        if not text:
            self.backlog_type         = "games"
            self.tiers: dict[str, int] = dict(DEFAULT_TIERS)
            self.items: list[Item]    = []
            return

        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {self.path.name}: {exc}") from exc

        if not isinstance(raw, dict) or "type" not in raw or "items" not in raw:
            raise ValueError(
                f"{self.path.name} is missing top-level 'type' or 'items'.\n"
                "  Expected format: { \"type\": \"games\", \"tiers\": {{...}}, \"items\": [...] }"
            )

        self.backlog_type = raw["type"]
        if self.backlog_type not in BACKLOG_TYPES:
            raise ValueError(
                f"Unknown type '{self.backlog_type}' in {self.path.name}. "
                f"Use: {', '.join(BACKLOG_TYPES)}"
            )

        # tiers: wheel-local definition, falls back to DEFAULT_TIERS
        raw_tiers = raw.get("tiers")
        if isinstance(raw_tiers, dict) and raw_tiers:
            self.tiers = {str(k): int(v) for k, v in raw_tiers.items()}
        else:
            self.tiers = dict(DEFAULT_TIERS)

        self.items = [Item(g, self.backlog_type) for g in raw["items"]]

# ----------------------------------- persistence -----------------------------------

    def save(self) -> None:
        out = {
            "type":  self.backlog_type,
            "tiers": self.tiers,
            "items": [i.to_dict() for i in self.items],
        }
        self.path.write_text(
            json.dumps(out, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

# ----------------------------------- querying --------------------------------------

    def available(self) -> list[Item]:
        """Items that can be spun (idle or incomplete)."""
        return [i for i in self.items if i.in_wheel]

    def find(self, name: str) -> Item | None:
        for item in self.items:
            if item.name == name:
                return item
        return None

    def tier_order(self) -> list[str]:
        """Tiers sorted highest weight first."""
        return sorted(self.tiers, key=lambda t: self.tiers[t], reverse=True)
    
    def set_status(self, item: Item, status: str) -> None:
        item.status = status
        self.save()

# ----------------------------------- picking -----------------------------------

    def pick_many(self, n: int) -> list[Item]:
        pool = self.available()
        if not pool:
            raise ValueError("No available items to pick from.")

        has_tiers = any(i.tier for i in pool)
        weighted  = (
            [item for item in pool for _ in range(item.weight(self.tiers))]
            if has_tiers
            else pool
        )

        picked: list[Item] = []
        seen: set[str]     = set()
        attempts           = 0
        max_attempts       = len(pool) * 20

        while len(picked) < min(n, len(pool)) and attempts < max_attempts:
            candidate = random.choice(weighted)
            if candidate.name not in seen:
                picked.append(candidate)
                seen.add(candidate.name)
            attempts += 1

        return picked


# ----------------------------------- helpers ---------------------------------------

def merge_roulettes(folder: Path, roulettes: list[Roulette]) -> Path:
    """Merge multiple Roulette objects into a new JSON in the roulettes folder."""
    roulettes_dir = folder / "roulettes"
    roulettes_dir.mkdir(exist_ok=True)

    stems = "_".join(r.path.stem for r in roulettes)
    path  = roulettes_dir / f"merge_{stems}.json"

    seen: set[str]     = set()
    merged: list[Item] = []
    for rou in roulettes:
        for item in rou.items:
            key = item.name.lower()
            if key not in seen:
                seen.add(key)
                merged.append(item)

    # use the first wheel's tiers for the merged file
    out = {
        "type":  roulettes[0].backlog_type,
        "tiers": roulettes[0].tiers,
        "items": [i.to_dict() for i in merged],
    }
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def list_roulettes(folder: Path, backlog_type: str) -> list[Path]:
    """Return all JSON files in roulettes/ whose top-level 'type' matches backlog_type."""
    roulettes_dir = folder / "roulettes"
    if not roulettes_dir.exists():
        return []
    result: list[Path] = []
    for f in sorted(roulettes_dir.glob("*.json")):
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and raw.get("type") == backlog_type:
                result.append(f)
        except (json.JSONDecodeError, KeyError):
            continue
    return result