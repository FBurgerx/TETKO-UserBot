"""ASCII-баннер TETKO с градиентом от красного к розовому."""
from __future__ import annotations


def _interpolate(start: tuple, end: tuple, t: float) -> tuple:
    """Линейная интерполяция между двумя RGB-цветами."""
    return tuple(int(s + (e - s) * t) for s, e in zip(start, end))


def _rgb_to_ansi(rgb: tuple) -> str:
    """Преобразовать RGB в ANSI escape-код (truecolor)."""
    r, g, b = rgb
    return f"\033[38;2;{r};{g};{b}m"


RESET = "\033[0m"
BOLD = "\033[1m"

# Цвета: красный -> розовый
COLOR_START = (220, 20, 20)     # ярко-красный
COLOR_END = (255, 105, 180)     # hot pink

# ASCII-арт TETKO (5 строк)
TETKO_ART = [
    r"  _____ _____ _____ _  __ ___  ",
    r" |_   _| ____|_   _| |/ / _ \ ",
    r"   | | |  _|   | | | ' / | | |",
    r"   | | | |___  | | | . \ |_| |",
    r"   |_| |_____| |_| |_|\_\___/ ",
]


def render_banner(version: str = "0.0.0.1", codename: str = "native") -> str:
    """Сгенерировать баннер с градиентом по горизонтали."""
    lines = []
    max_len = max(len(line) for line in TETKO_ART)

    for line in TETKO_ART:
        colored_line = ""
        for i, char in enumerate(line):
            # прогресс 0..1 по длине строки
            t = i / max(len(line) - 1, 1)
            rgb = _interpolate(COLOR_START, COLOR_END, t)
            colored_line += _rgb_to_ansi(rgb) + char
        lines.append(colored_line + RESET)

    # Подпись снизу — тоже градиент
    subtitle = f"  TETKO UserBot  v{version}  ({codename})"
    sub_colored = ""
    for i, char in enumerate(subtitle):
        t = i / max(len(subtitle) - 1, 1)
        rgb = _interpolate(COLOR_START, COLOR_END, t)
        sub_colored += _rgb_to_ansi(rgb) + char

    return "\n".join(lines) + "\n" + sub_colored + RESET


def print_banner(version: str = "0.0.0.1", codename: str = "native") -> None:
    """Напечатать баннер в stdout."""
    print(render_banner(version, codename))
    print()


if __name__ == "__main__":
    print_banner()
