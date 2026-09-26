"""ANSI color and styling helpers for terminal output.

Use the `color()` function for custom styles or the convenience helpers
like `success()`, `error()`, `info()`, and `warning()` across processes.
"""
from typing import Optional, Iterable
import re
import sys

RESET = "\033[0m"

_FG_CODES = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "bright_black": 90,
    "bright_red": 91,
    "bright_green": 92,
    "bright_yellow": 93,
    "bright_blue": 94,
    "bright_magenta": 95,
    "bright_cyan": 96,
    "bright_white": 97,
}

_BG_CODES = {}
for name, code in _FG_CODES.items():
    if name.startswith("bright_"):
        bg_name = name.replace("bright_", "on_bright_")
        _BG_CODES[bg_name] = code + 10
    else:
        bg_name = "on_" + name
        _BG_CODES[bg_name] = code + 10

FG = {k: str(v) for k, v in _FG_CODES.items()}
BG = {k: str(v) for k, v in _BG_CODES.items()}

STYLES = {
    "bold": "1",
    "dim": "2",
    "italic": "3",
    "underline": "4",
    "blink": "5",
    "reverse": "7",
    "hidden": "8",
    "strike": "9",
}

_ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def _escape(codes: Iterable[str]) -> str:
    codes = [c for c in codes if c]
    if not codes:
        return ""
    return f"\033[{';'.join(codes)}m"


def color(text: str, fg: Optional[str] = None, bg: Optional[str] = None, style: Optional[str | Iterable[str]] = None) -> str:
    """Return `text` wrapped in ANSI escapes.

    - `fg` accepts keys from `FG` (e.g. "red", "bright_blue").
    - `bg` accepts keys from `BG` (e.g. "on_red", "on_bright_blue").
    - `style` accepts a single style name or an iterable of style names from `STYLES`.
    """
    codes: list[str] = []
    if style:
        if isinstance(style, str):
            names = [style]
        else:
            names = list(style)
        for name in names:
            val = STYLES.get(name)
            if val:
                codes.append(val)
    if fg:
        val = FG.get(fg)
        if val:
            codes.append(val)
    if bg:
        val = BG.get(bg)
        if val:
            codes.append(val)

    if not codes:
        return text
    return f"{_escape(codes)}{text}{RESET}"


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from `text`."""
    return _ANSI_RE.sub("", text)


def supports_color(stream=None) -> bool:
    """Return True if `stream` supports ANSI colors (isatty)."""
    if stream is None:
        stream = sys.stdout
    return hasattr(stream, "isatty") and stream.isatty()


# Convenience helpers
def bold(text: str) -> str:
    return color(text, style="bold")


def underline(text: str) -> str:
    return color(text, style="underline")


def dim(text: str) -> str:
    return color(text, style="dim")


def success(text: str) -> str:
    return color(text, fg="green", style="bold")


def error(text: str) -> str:
    return color(text, fg="bright_red", style=["bold"]) 


def warning(text: str) -> str:
    return color(text, fg="yellow", style="bold")


def info(text: str) -> str:
    return color(text, fg="cyan")


__all__ = [
    "color",
    "strip_ansi",
    "supports_color",
    "bold",
    "underline",
    "dim",
    "success",
    "error",
    "warning",
    "info",
    "FG",
    "BG",
    "STYLES",
    "RESET",
]
