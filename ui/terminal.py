"""
ui/terminal.py
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

from constants import (
    BACKLOG_TYPES, TYPE_LABELS, SETTINGS_META,
    _Back, QUIT_WORDS, BACK_WORDS, DEFAULT_SETTINGS,
    BLOCK_CATEGORY, BLOCK_WHEEL,
    STATUS_DONE, STATUS_DROPPED, STATUS_INCOMPLETE,
    EVENT_SPUN, EVENT_FINISHED, EVENT_INCOMPLETE, EVENT_DROPPED,
)
from ansi import (
    header, option, error, success, info,
    bold, muted, ghost, tier_style_indexed, cyan, green, pink,
    prompt_prefix, main, style, BOLD, _CYAN, _GREEN,
)
from display import display_item, spin_animation
from history import append_event, load_history
from actives import (
    load_actives,
    get_active_for_category,
    get_active_for_wheel,
    add_active,
    remove_active,
)
from models import Item
from roulette import Roulette, list_roulettes, merge_roulettes
from settings import save_settings, get_last_spinned, set_last_spinned


# -- I/O helpers ---------------------------------------------------------------

def _prompt(hint: str = "") -> str:
    if hint:
        print(ghost(f"  {hint}"))
    print(prompt_prefix(), end="", flush=True)
    return input().strip()


def _clr() -> None:
    subprocess.run(
        ["cls"] if os.name == "nt" else ["clear"],
        shell=True,
        check=False
    )


def _is_quit(raw: str) -> bool:
    return raw.lower() in QUIT_WORDS


def _is_back(raw: str) -> bool:
    return raw.lower() in BACK_WORDS


def _quit() -> None:
    _clr()
    print(f"\n  {ghost('Goodbye!')}\n")
    sys.exit(0)


def _check_global(raw: str) -> None:
    if _is_quit(raw):
        _quit()
    if _is_back(raw):
        raise _Back()


def _pause(msg: str = "Press Enter to continue.") -> None:
    input(ghost(f"\n  {msg}  [Enter]"))


def _ask_rating() -> int | None:
    raw = _prompt("Rate it 1-5  (Enter to skip)")
    if not raw or _is_back(raw) or _is_quit(raw):
        return None
    try:
        val = int(raw)
        if 1 <= val <= 5:
            return val
    except ValueError:
        pass
    return None


def _show_err(msg: str | None) -> None:
    """Print a pending error line if one exists, then a blank line."""
    if msg:
        print(error(msg))
        print()



def _tier_counts_str(
    items:      list[Item],
    tier_order: list[str],
    available_only: bool = True,
) -> str:
    pool = [i for i in items if i.in_wheel] if available_only else items
    parts = []
    for idx, t in enumerate(tier_order):
        count = sum(1 for i in pool if i.tier == t)
        label = tier_style_indexed(t, f"{t}:{count}", idx)
        parts.append(label)
    return "  ".join(parts)


# -- settings screen -----------------------------------------------------------

def screen_settings(folder: Path, settings: dict, crumbs: list[str]) -> dict:
    my_crumbs = crumbs + ["Settings"]
    pending_err: str | None = None

    while True:
        _clr()
        print(header(my_crumbs))
        print()

        label_w = max(len(m["label"]) for m in SETTINGS_META) + 2

        for i, meta in enumerate(SETTINGS_META, 1):
            val     = settings[meta["key"]]
            label   = f"{meta['label']:<{label_w}}"
            val_str = cyan(str(val))
            hint    = meta.get("description", "")
            print(f"  {green(f'[{i}]')}  {main(label)}{val_str}  {ghost(hint)}")

        print()
        print(option("r", "Reset to defaults"))
        print(option("b / q", "Back / Quit"))
        print()
        _show_err(pending_err)
        pending_err = None

        raw = _prompt("Setting number, or  r  to reset")
        if _is_quit(raw): _quit()
        if _is_back(raw): return settings

        if raw.lower() == "r":
            ans = _prompt("Reset all settings to defaults?  (y/N)")
            if ans.lower() == "y":
                settings = dict(DEFAULT_SETTINGS)
                save_settings(folder, settings)
                print(success("Settings reset to defaults."))
            _pause()
            continue

        try:
            idx = int(raw) - 1
            if not (0 <= idx < len(SETTINGS_META)):
                raise ValueError
        except ValueError:
            pending_err = "Invalid choice."
            continue

        meta    = SETTINGS_META[idx]
        current = settings[meta["key"]]
        print(info(f"{meta['label']}: {current}  -  {meta.get('description', '')}"))

        if meta.get("choices"):
            choices = meta["choices"]
            for ci, ch in enumerate(choices, 1):
                marker = green("✓") if ch == current else " "
                print(f"  {green(f'[{ci}]')}  {marker}  {main(ch)}")
            raw_val = _prompt("Choose number")
            if not raw_val or _is_back(raw_val):
                continue
            try:
                cidx = int(raw_val) - 1
                if not (0 <= cidx < len(choices)):
                    raise ValueError
                new_val = choices[cidx]
            except ValueError:
                pending_err = "Invalid choice."
                continue
        else:
            raw_val = _prompt(f"New value  (Enter to keep  {current})")
            if not raw_val or _is_back(raw_val):
                continue
            try:
                if meta["type"] == "int":
                    new_val = int(raw_val)
                elif meta["type"] == "float":
                    new_val = round(float(raw_val), 2)
                else:
                    new_val = raw_val
            except ValueError:
                pending_err = f"Expected {meta['type']}."
                continue

        settings[meta["key"]] = new_val
        save_settings(folder, settings)
        print(success(f"{meta['label']} → {new_val}"))


# -- history screen ------------------------------------------------------------

def screen_history(folder: Path, crumbs: list[str]) -> None:
    my_crumbs     = crumbs + ["History"]
    history       = load_history(folder)
    active_filter: str | None = None
    pending_err:   str | None = None

    while True:
        _clr()
        print(header(my_crumbs))

        if not history:
            print(info("No history yet. Spin something first!"))
            print()
            print(option("b / q", "Back / Quit"))
            raw = _prompt()
            if _is_quit(raw): _quit()
            return

        sources = sorted(set(e["wheel"] for e in history))

        displayed = history if not active_filter else [
            e for e in history if e.get("wheel") == active_filter
        ]

        print()
        if active_filter:
            print(info(f"Filter: {active_filter}  (f to change, c to clear)"))
        else:
            print(info(f"{len(history)} entries  ·  f to filter by wheel"))

        print(muted("  " + "-" * 52))

        for entry in reversed(displayed[-20:]):
            ts     = muted(entry.get("timestamp", "")[:10])
            evt    = entry.get("event", "")
            name   = entry.get("item_name", "")
            wheel  = muted(f"[{entry.get('wheel', '')}]")
            rating = f"  {green(str(entry['rating']) + '/5')}" if entry.get("rating") else ""

            evt_col = {
                "spun":       cyan,
                "finished":   green,
                "dropped":    pink,
                "incomplete": lambda t: muted(t),
            }.get(evt, main)

            print(f"  {ts}  {evt_col(f'{evt:<12}')}{main(f'{name:<32}')}{rating}  {wheel}")

        if len(displayed) > 20:
            print(muted(f"  … and {len(displayed) - 20} older entries"))

        print()
        print(option("f", "Filter by wheel"))
        if active_filter:
            print(option("c", "Clear filter"))
        print(option("b / q", "Back / Quit"))
        print()
        _show_err(pending_err)
        pending_err = None

        raw = _prompt()
        if _is_quit(raw): _quit()
        if _is_back(raw): return

        if raw.lower() == "c":
            active_filter = None
            continue

        if raw.lower() == "f":
            _clr()
            print(header(my_crumbs + ["Filter"]))
            print()
            for i, src in enumerate(sources, 1):
                print(option(str(i), src))
            print(option("b", "Cancel"))
            raw2 = _prompt("Wheel number")
            if _is_quit(raw2): _quit()
            if _is_back(raw2): continue
            try:
                idx = int(raw2) - 1
                if not (0 <= idx < len(sources)):
                    raise ValueError
                active_filter = sources[idx]
            except ValueError:
                pending_err = "Invalid choice."
            continue

        pending_err = "Invalid choice."


# -- active item screen --------------------------------------------------------

def screen_active_item(folder: Path, active: dict, crumbs: list[str]) -> None:
    category  = active["category"]
    wheel     = active["wheel"]
    item_name = active["item_name"]
    spun_at   = active.get("spun_at", "")
    my_crumbs = crumbs + ["Active"]

    wheel_path = folder / "roulettes" / wheel
    try:
        roulette = Roulette(wheel_path)
    except Exception as exc:
        print(error(f"Could not load wheel: {exc}"))
        _pause()
        return

    item = roulette.find(item_name)
    if item is None:
        print(error(f'"{item_name}" not found in {wheel}. Clearing stale active entry.'))
        remove_active(folder, category, wheel, item_name)
        _pause()
        return

    pending_err: str | None = None

    while True:
        _clr()
        print(header(my_crumbs))
        print(muted(f"  Active since: {spun_at[:10]}"))
        display_item(item, tiers=roulette.tiers)
        print()
        print(option("f", "Finish"))
        print(option("d", "Drop"))
        print(option("b / q", "Back / Quit"))
        print()
        _show_err(pending_err)
        pending_err = None

        raw = _prompt()
        if _is_quit(raw): _quit()
        if _is_back(raw): return

        if raw.lower() == "f":
            print(info("Nice! How was it?"))
            rating = _ask_rating()
            roulette.set_status(item, STATUS_DONE)
            remove_active(folder, category, wheel, item_name)
            append_event(folder, item, wheel, EVENT_FINISHED, rating)
            rating_str = f"  {green(str(rating) + '/5')}" if rating else ""
            print(success(f'"{item_name}" marked as finished.{rating_str}'))
            _pause()
            return

        if raw.lower() == "d":
            raw2 = _prompt("Keep in the wheel for later?  (Y/n)")
            if _is_quit(raw2): _quit()
            keep = raw2.lower() != "n"

            if keep:
                roulette.set_status(item, STATUS_INCOMPLETE)
                remove_active(folder, category, wheel, item_name)
                append_event(folder, item, wheel, EVENT_INCOMPLETE)
                print(success(f'"{item_name}" kept in the wheel.'))
                _pause()
                return
            else:
                print(info("Last chance - how was it?"))
                rating = _ask_rating()
                roulette.set_status(item, STATUS_DROPPED)
                remove_active(folder, category, wheel, item_name)
                append_event(folder, item, wheel, EVENT_DROPPED, rating)
                rating_str = f"  {green(str(rating) + '/5')}" if rating else ""
                print(success(f'"{item_name}" dropped.{rating_str}'))
                _pause()
                return

        pending_err = "Invalid choice."


# -- main menu -----------------------------------------------------------------

def screen_main_menu(folder: Path, settings: dict) -> tuple[str, dict]:
    crumbs      = ["Backlog Roulette"]
    pending_err: str | None = None

    while True:
        _clr()
        last = get_last_spinned(folder)

        print(header(crumbs))
        print()

        if last:
            print(option("Enter", f'Quick spin  "{last}"'))
            print()

        for i, label in enumerate(TYPE_LABELS, 1):
            print(option(str(i), label))

        print()
        print(option("h", "History"))
        print(option("s", "Settings"))
        print(option("q", "Quit"))
        print()
        _show_err(pending_err)
        pending_err = None

        raw = _prompt(
            "Choose a category, or Enter for quick spin" if last else "Choose a category"
        )

        if _is_quit(raw): _quit()

        if raw == "" and last:
            return "__quickspin__", settings

        if raw.lower() == "h":
            try:
                screen_history(folder, crumbs)
            except _Back:
                pass
            continue

        if raw.lower() == "s":
            try:
                settings = screen_settings(folder, settings, crumbs)
            except _Back:
                pass
            continue

        try:
            idx = int(raw) - 1
            if not (0 <= idx < len(BACKLOG_TYPES)):
                raise ValueError
        except ValueError:
            pending_err = "Invalid choice."
            continue

        return BACKLOG_TYPES[idx], settings


# -- roulette selector ---------------------------------------------------------

def screen_select_roulette(folder: Path, backlog_type: str, crumbs: list[str]) -> Roulette:
    my_crumbs   = crumbs + [backlog_type.capitalize()]
    pending_err: str | None = None

    while True:
        type_files = list_roulettes(folder, backlog_type)
        _clr()
        print(header(my_crumbs))
        print()

        if not type_files:
            print(error(f"No {backlog_type} wheels found in  roulettes/"))
            print(ghost("  Create a JSON there with  \"type\": \"" + backlog_type + "\""))
            print()
            print(option("b / q", "Back / Quit"))
            raw = _prompt()
            _check_global(raw)
            raise _Back()

        rows: list[dict] = []
        all_tier_orders: list[list[str]] = []

        for f in type_files:
            try:
                rou        = Roulette(f)
                avail      = len(rou.available())
                done       = sum(1 for it in rou.items if it.status == STATUS_DONE)
                tier_order = rou.tier_order()
                has_tiers  = any(it.tier for it in rou.items)
                active_tag = get_active_for_wheel(folder, backlog_type, f.name)
                rows.append({
                    "f": f, "rou": rou, "avail": avail, "done": done,
                    "tier_order": tier_order, "has_tiers": has_tiers,
                    "active": active_tag, "ok": True,
                })
                all_tier_orders.append(tier_order)
            except Exception:
                rows.append({"f": f, "ok": False})
                all_tier_orders.append([])

        seen_tiers: list[str] = []
        for order in all_tier_orders:
            for t in order:
                if t not in seen_tiers:
                    seen_tiers.append(t)

        name_w  = max((len(r["f"].stem.replace("_", " ")) for r in rows), default=20) + 2
        avail_w = max((len(str(r.get("avail", 0))) for r in rows if r["ok"]), default=2)
        done_w  = max((len(str(r.get("done",  0))) for r in rows if r["ok"]), default=2)

        for i, row in enumerate(rows, 1):
            if not row["ok"]:
                print(f"  {green(f'[{i}]')}  {main(row['f'].stem.replace('_', ' '))}  {error('(error loading)')}")
                continue

            f          = row["f"]
            rou        = row["rou"]
            avail      = row["avail"]
            done       = row["done"]
            tier_order = row["tier_order"]
            has_tiers  = row["has_tiers"]
            active_tag = f"  {cyan('[active]')}" if row["active"] else ""

            name_col  = main(f.stem.replace("_", " "))
            avail_col = f"{avail:>{avail_w}} left"
            done_col  = f"{done:>{done_w}} done"

            if has_tiers:
                tier_parts: list[str] = []
                for idx, t in enumerate(seen_tiers):
                    count     = sum(1 for it in rou.available() if it.tier == t)
                    local_idx = tier_order.index(t) if t in tier_order else len(tier_order)
                    label     = tier_style_indexed(t, f"{t}:{count}", local_idx)
                    raw_label = f"{t}:{count}"
                    pad       = " " * (len(f"{t}:00") - len(raw_label))
                    tier_parts.append(label + pad)
                tier_col = "  ".join(tier_parts)
                stats = f"{muted(avail_col)}  {tier_col}  {muted(done_col)}"
            else:
                stats = f"{muted(avail_col)}  {muted(done_col)}"

            name_pad = name_w - len(f.stem.replace("_", " "))
            print(f"  {green(f'[{i}]')}  {name_col}{' ' * name_pad}  {stats}{active_tag}")

        merge_available = len(type_files) > 1
        print()
        if merge_available:
            print(option("m", "Merge wheels", "e.g.  m 1,2,3"))
        print(option("b / q", "Back / Quit"))
        print()
        _show_err(pending_err)
        pending_err = None

        raw = _prompt("Choose wheel")
        if _is_quit(raw): _quit()
        if _is_back(raw): raise _Back()

        if raw.lower().startswith("m") and merge_available:
            parts = raw[1:].replace(" ", "").split(",")
            try:
                indices = [int(p) - 1 for p in parts if p]
                if not indices or any(not (0 <= i < len(type_files)) for i in indices):
                    raise ValueError
            except ValueError:
                pending_err = "Invalid merge selection.  Example: m 1,2"
                continue

            roulettes  = [Roulette(type_files[i]) for i in indices]
            merge_path = merge_roulettes(folder, roulettes)
            stems      = ", ".join(type_files[i].stem.replace("_", " ") for i in indices)
            print(success(f"Merged → {merge_path.name}  (sources: {stems})"))
            continue

        try:
            idx = int(raw) - 1
            if not (0 <= idx < len(type_files)):
                raise ValueError
        except ValueError:
            pending_err = "Invalid choice."
            continue

        try:
            return Roulette(type_files[idx])
        except (FileNotFoundError, ValueError) as exc:
            pending_err = str(exc)
            continue


# -- spin loop -----------------------------------------------------------------

def run_roulette(
    roulette: Roulette,
    settings: dict,
    folder:   Path,
    crumbs:   list[str],
) -> None:
    my_crumbs    = crumbs + [roulette.path.stem.replace("_", " ")]
    reroll_limit = settings["reroll_limit"]
    top_x        = settings["top_x"]
    anim_steps   = settings["animation_steps"]
    anim_speed   = settings["animation_speed"]
    tier_order   = roulette.tier_order()
    pending_err: str | None = None

    rerolls_left = reroll_limit

    while True:
        available = roulette.available()

        _clr()
        print(header(my_crumbs))
        print()

        avail_str  = cyan(str(len(available)))
        reroll_str = (
            f"  {ghost('·')}  {ghost('Rerolls left:')} {cyan(str(rerolls_left))}"
            if rerolls_left >= 0 else ""
        )
        print(f"  {ghost('Items remaining:')} {avail_str}{reroll_str}")

        if any(i.tier for i in available):
            tier_parts = []
            for idx, t in enumerate(tier_order):
                count = sum(1 for i in available if i.tier == t)
                tier_parts.append(tier_style_indexed(t, f"{t}: {count}", idx))
            print(f"  {'  '.join(tier_parts)}")

        print()
        print(option("Enter", "Spin!"))
        print(option("b / q", "Back / Quit"))
        print()
        _show_err(pending_err)
        pending_err = None

        raw = _prompt()
        if _is_quit(raw): _quit()
        if _is_back(raw): return

        if raw != "":
            pending_err = "Invalid choice."
            continue

        if not available:
            print(error("No items left in this wheel. Well done!"))
            _pause()
            return

        spin_animation(anim_steps, anim_speed)

        pick_count = min(top_x, len(available))
        picked     = roulette.pick_many(pick_count)

        chosen_item: Item | None = None

        if len(picked) == 1:
            display_item(picked[0], tiers=roulette.tiers)
            chosen_item = picked[0]

            if rerolls_left > 0 or rerolls_left == -1:
                raw = _prompt("Reroll?  (y / N)")
                if _is_quit(raw): _quit()
                if _is_back(raw): return
                if raw.lower() == "y":
                    if rerolls_left > 0:
                        rerolls_left -= 1
                    continue
        else:
            print()
            for i, item in enumerate(picked, 1):
                display_item(item, index=i, tiers=roulette.tiers)

            if rerolls_left > 0 or rerolls_left == -1:
                raw = _prompt("Reroll all?  (y / N  or pick a number)")
                if _is_quit(raw): _quit()
                if _is_back(raw): return
                if raw.lower() == "y":
                    if rerolls_left > 0:
                        rerolls_left -= 1
                    continue
                try:
                    idx = int(raw) - 1
                    chosen_item = picked[idx] if 0 <= idx < len(picked) else picked[0]
                except ValueError:
                    chosen_item = picked[0]
            else:
                raw = _prompt(f"Pick one  (1–{len(picked)})")
                if _is_quit(raw): _quit()
                if _is_back(raw): return
                try:
                    idx = int(raw) - 1
                    chosen_item = picked[idx] if 0 <= idx < len(picked) else picked[0]
                except ValueError:
                    chosen_item = picked[0]

        if chosen_item is not None:
            add_active(folder, roulette.backlog_type, roulette.path.name, chosen_item.name)
            append_event(folder, chosen_item, roulette.path.name, EVENT_SPUN)
            set_last_spinned(folder, roulette.path.stem)
            print(success(f'"{chosen_item.name}" is your active {roulette.backlog_type}. Go enjoy it!'))
            _pause()
            return


# -- app loop ------------------------------------------------------------------

def run_app(folder: Path, settings: dict) -> None:
    (folder / "roulettes").mkdir(exist_ok=True)
    (folder / "data").mkdir(exist_ok=True)

    while True:
        backlog_type, settings = screen_main_menu(folder, settings)
        crumbs = ["Backlog Roulette"]

        if backlog_type == "__quickspin__":
            stem = get_last_spinned(folder)
            if not stem:
                continue
            found = next((f for f in (folder / "roulettes").glob("*.json") if f.stem == stem), None)
            if not found:
                continue
            try:
                rou = Roulette(found)
                _handle_category_entry(folder, rou.backlog_type, settings, crumbs, quick_wheel=rou)
            except _Back:
                pass
            continue

        _handle_category_entry(folder, backlog_type, settings, crumbs)


def _handle_category_entry(
    folder:       Path,
    backlog_type: str,
    settings:     dict,
    crumbs:       list[str],
    quick_wheel:  Roulette | None = None,
) -> None:
    block_mode  = settings.get("block_mode", BLOCK_CATEGORY)
    type_crumbs = crumbs + [backlog_type.capitalize()]

    if block_mode == BLOCK_CATEGORY:
        active = get_active_for_category(folder, backlog_type)
        if active:
            screen_active_item(folder, active, type_crumbs)
            return
        if quick_wheel:
            try:
                run_roulette(quick_wheel, settings, folder, type_crumbs)
            except _Back:
                pass
        else:
            while True:
                try:
                    roulette = screen_select_roulette(folder, backlog_type, crumbs)
                except _Back:
                    break
                try:
                    run_roulette(roulette, settings, folder, type_crumbs)
                except _Back:
                    pass
                if get_active_for_category(folder, backlog_type):
                    break

    else:  # BLOCK_WHEEL
        if quick_wheel:
            active = get_active_for_wheel(folder, backlog_type, quick_wheel.path.name)
            if active:
                screen_active_item(folder, active, type_crumbs)
            else:
                try:
                    run_roulette(quick_wheel, settings, folder, type_crumbs)
                except _Back:
                    pass
        else:
            while True:
                try:
                    roulette = screen_select_roulette(folder, backlog_type, crumbs)
                except _Back:
                    break
                active = get_active_for_wheel(folder, backlog_type, roulette.path.name)
                if active:
                    screen_active_item(folder, active, type_crumbs)
                else:
                    try:
                        run_roulette(roulette, settings, folder, type_crumbs)
                    except _Back:
                        pass
                if get_active_for_wheel(folder, backlog_type, roulette.path.name):
                    break