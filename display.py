"""
display.py -- pure output helpers, no user input.
"""

from __future__ import annotations

import time

from models import Item
from ansi import main, muted, cyan, tier_style_indexed, style, _WHITE_DIM


def display_item(item: Item, index: int | None = None, tiers: dict[str, int] | None = None) -> None:
    prefix = f"[{index}] " if index is not None else ""

    tier_order = sorted(tiers, key=lambda t: tiers[t], reverse=True) if tiers else ["S", "A", "B"]
    tier_idx   = tier_order.index(item.tier) if item.tier and item.tier in tier_order else len(tier_order)

    lines: list[tuple[str, str]] = [(f"{prefix}NAME", main(item.name))]

    if item.series:
        lines.append(("SERIES", main(" › ".join(item.series))))

    if item.backlog_type == "games":
        if item.estimated_hours is not None:
            lines.append(("EST. HOURS", main(f"~{item.estimated_hours}h")))
        if item.completion_condition:
            lines.append(("COMPLETE", main(item.completion_condition)))
    elif item.backlog_type == "movies":
        if item.runtime_minutes is not None:
            h, m = divmod(item.runtime_minutes, 60)
            lines.append(("RUNTIME", main(f"{h}h {m:02d}m")))
    elif item.backlog_type == "books":
        if item.pages is not None:
            lines.append(("PAGES", main(str(item.pages))))

    if item.tier:
        lines.append(("TIER", tier_style_indexed(item.tier, item.tier, tier_idx)))

    if item.note:
        lines.append(("NOTE", main(item.note)))

    if item.status != "idle":
        lines.append(("STATUS", main(item.status.upper())))

    rule = style("  " + "-" * 52, _WHITE_DIM)
    print(f"\n{rule}")
    for label, value in lines:
        print(f"  {muted(f'{label:<14}')}{value}")
    print(rule)


def spin_animation(steps: int, speed: float) -> None:
    print(f"\n  {muted('Spinning')}", end="", flush=True)
    for _ in range(steps):
        time.sleep(speed)
        print(muted("."), end="", flush=True)
    print()