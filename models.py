"""
models.py
Represents a single backlog entry (game, movie, or book).
"""

from __future__ import annotations

from constants import (
    STATUS_IDLE, STATUS_DONE, STATUS_DROPPED, STATUS_INCOMPLETE,
    DEFAULT_TIERS,
)


class Item:
    def __init__(self, data: dict, backlog_type: str) -> None:
        data                      = Item._migrate_status(data)
        self.backlog_type         = backlog_type
        self.name                 = data["name"]
        self.tier                 = data.get("tier")
        self.series               = data.get("series", [])
        self.note                 = data.get("note")
        self.status               = data.get("status", STATUS_IDLE)
        self.estimated_hours      = data.get("estimated_hours")
        self.runtime_minutes      = data.get("runtime_minutes")
        self.pages                = data.get("pages")
        self.completion_condition = data.get("completion_condition")

    @staticmethod
    def _migrate_status(data: dict) -> dict:
        """Back-compat: old JSONs used done: true/false."""
        if "status" not in data and "done" in data:
            data = dict(data)
            data["status"] = STATUS_DONE if data.pop("done") else STATUS_IDLE
        return data

    @property
    def in_wheel(self) -> bool:
        """True if this item should appear in spin pool."""
        return self.status in (STATUS_IDLE, STATUS_INCOMPLETE)

    def weight(self, tiers: dict[str, int] | None = None) -> int:
        """
        Return the spin weight for this item given the wheel's tier map.
        Falls back to DEFAULT_TIERS, then to the minimum defined weight
        if the item's tier isn't in the map at all.
        """
        t = tiers or DEFAULT_TIERS
        if self.tier and self.tier in t:
            return t[self.tier]
        if self.tier and t:
            # unknown tier gets the lowest defined weight
            return min(t.values())
        # no tier at all, equal weight, (use middle of the map or 15)
        return min(t.values()) if t else 15

    def to_dict(self) -> dict:
        d: dict = {"name": self.name, "status": self.status}

        if self.backlog_type == "games":
            if self.estimated_hours is not None:
                d["estimated_hours"] = self.estimated_hours
            if self.completion_condition is not None:
                d["completion_condition"] = self.completion_condition
        elif self.backlog_type == "movies":
            if self.runtime_minutes is not None:
                d["runtime_minutes"] = self.runtime_minutes
        elif self.backlog_type == "books":
            if self.pages is not None:
                d["pages"] = self.pages

        if self.tier is not None:
            d["tier"] = self.tier
        if self.series:
            d["series"] = self.series
        if self.note is not None:
            d["note"] = self.note

        return d