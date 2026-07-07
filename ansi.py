"""
ansi.py
"""

from __future__ import annotations

# reset
RESET = "\033[0m"

# styles
BOLD   = "\033[1m"
DIM    = "\033[2m"
ITALIC = "\033[3m"


def _rgb(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


# palette -- no greys anywhere
_CYAN      = _rgb(0,   229, 255)   # #00e5ff
_PINK      = _rgb(255,  46, 136)   # #ff2e88
_GREEN     = _rgb(124, 255,   0)   # #7cff00
_YELLOW    = _rgb(255, 220,  50)   # #ffdc32
_WHITE     = _rgb(230, 230, 230)   # #e6e6e6
_WHITE_DIM = _rgb(160, 160, 160)   # #a0a0a0


def style(text: str, *codes: str) -> str:
    return "".join(codes) + text + RESET


# base styles
def bold(text: str)   -> str: return style(text, BOLD)
def italic(text: str) -> str: return style(text, ITALIC)
def dim(text: str)    -> str: return style(text, DIM)

# named colours
def cyan(text: str)   -> str: return style(text, _CYAN)
def pink(text: str)   -> str: return style(text, _PINK)
def green(text: str)  -> str: return style(text, _GREEN)
def white(text: str)  -> str: return style(text, _WHITE)

# aliases -- everything that was grey/muted/ghost now maps to white variants
def main(text: str)   -> str: return style(text, _WHITE)          # primary text
def muted(text: str)  -> str: return style(text, _WHITE_DIM)      # secondary text, still white
def ghost(text: str)  -> str: return style(text, _WHITE_DIM)      # same as muted legacy ah code


def tier_style_indexed(tier: str | None, text: str, index: int) -> str:
    """Colour a tier label by its position in the wheel's tier list (highest weight first)."""
    _TIER_PALETTE = [
        _YELLOW + BOLD,   # 0 – top tier
        _CYAN   + BOLD,   # 1
        _PINK,            # 2
        _GREEN,           # 3
        _WHITE,           # 4
        _WHITE_DIM,       # 5+
    ]
    code = _TIER_PALETTE[min(index, len(_TIER_PALETTE) - 1)]
    return style(text, code)


def error(text: str)   -> str: return style(f"  ✗  {text}", _PINK)
def success(text: str) -> str: return style(f"  ✓  {text}", _GREEN)
def info(text: str)    -> str: return style(f"  {text}", _WHITE_DIM)


def breadcrumb(parts: list[str]) -> str:
    """Last part = cyan+bold (current page). Parents = dimmed white."""
    if not parts:
        return ""
    *parents, current = parts
    sep    = style(" › ", _WHITE_DIM)
    pieces = [style(p, _WHITE_DIM) for p in parents]
    pieces.append(style(current, _CYAN, BOLD))
    return "  " + sep.join(pieces)


def header(crumbs: list[str]) -> str:
    lines: list[str] = [""]
    if crumbs:
        lines.append(breadcrumb(crumbs))
    lines.append(style("  " + "-" * 52, _WHITE_DIM))
    return "\n".join(lines)


def option(key: str, label: str, hint: str = "") -> str:
    k = style(f"[{key}]", _GREEN)
    h = f"  {style(hint, _WHITE_DIM)}" if hint else ""
    return f"  {k}  {style(label, _WHITE)}{h}"


def prompt_prefix() -> str:
    return f"\n  {style('›', BOLD, _CYAN)} "