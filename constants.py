from __future__ import annotations


class _Back(Exception):
    pass


QUIT_WORDS = {"q", "quit", "exit"}
BACK_WORDS = {"b", "back"}

BACKLOG_TYPES = ["games", "movies", "books"]
TYPE_LABELS   = ["Games", "Movies", "Books"]

# Fallback tier weights used when a wheel JSON has no "tiers" key
DEFAULT_TIERS: dict[str, int] = {"S": 50, "A": 35, "B": 15}

STATUS_IDLE       = "idle"
STATUS_DONE       = "done"
STATUS_DROPPED    = "dropped"
STATUS_INCOMPLETE = "incomplete"

BLOCK_CATEGORY = "category"
BLOCK_WHEEL    = "wheel"

EVENT_SPUN       = "spun"
EVENT_FINISHED   = "finished"
EVENT_INCOMPLETE = "incomplete"
EVENT_DROPPED    = "dropped"

DEFAULT_SETTINGS: dict = {
    "reroll_limit":    3,
    "top_x":           3,
    "animation_steps": 6,
    "animation_speed": 0.3,
    "block_mode":      BLOCK_CATEGORY,
}

SETTINGS_META = [
    {
        "key":         "reroll_limit",
        "label":       "Reroll limit",
        "description": "Max rerolls per spin. -1 = unlimited.",
        "type":        "int",
    },
    {
        "key":         "top_x",
        "label":       "Top X",
        "description": "How many items to show per spin.",
        "type":        "int",
    },
    {
        "key":         "animation_steps",
        "label":       "Animation steps",
        "description": "Number of dots in the spin animation.",
        "type":        "int",
    },
    {
        "key":         "animation_speed",
        "label":       "Animation speed",
        "description": "Seconds between animation dots.",
        "type":        "float",
    },
    {
        "key":         "block_mode",
        "label":       "Block mode",
        "description": "category = one active per type.  wheel = one active per wheel.",
        "type":        "str",
        "choices":     [BLOCK_CATEGORY, BLOCK_WHEEL],
    },
]