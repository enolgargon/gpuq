import sys
import os

USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ

RESET = "\033[0m"
BOLD = "\033[1m"

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BLUE = "\033[34m"
GREY = "\033[90m"


STATUS_COLORS = {
    "queued": YELLOW,
    "running": GREEN,
    "finished": BLUE,
    "failed": RED,
    "canceled": GREY,
}


def _colorize(text: str, color: str) -> str:
    if not USE_COLOR:
        return text
    return f"{color}{text}{RESET}"


def bold(text: str) -> str:
    if not USE_COLOR:
        return text
    return f"{BOLD}{text}{RESET}"


def status(text: str) -> str:
    color = STATUS_COLORS.get(text)
    if not color:
        return text
    return _colorize(text, color)


def error(text: str) -> str:
    return _colorize(text, RED)


def warning(text: str) -> str:
    return _colorize(text, YELLOW)