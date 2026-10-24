f = open("log.log", "a+")
TARGET_FPS = 60

KEYS = {
    "q": ord("q"),
    "Q": ord("Q"),
}

BORDERS = {
    "rounded": {
        "top-left"    : "╭",
        "top-right"   : "╮",
        "bottom-left" : "╰",
        "bottom-right": "╯",
        "horizontal"  : "─",
        "vertical"    : "│",
    },
    "sharp": {
        "top-left"    : "┌",
        "top-right"   : "┐",
        "bottom-left" : "└",
        "bottom-right": "┘",
        "horizontal"  : "─",
        "vertical"    : "│",
    },
    "double": {
        "top-left"    : "╔",
        "top-right"   : "╗",
        "bottom-left" : "╚",
        "bottom-right": "╝",
        "horizontal"  : "═",
        "vertical"    : "║",
    },
}


def is_key(key: int, chk_against: tuple[str]) -> bool:
    all_chk_values = (KEYS[i] for i in chk_against)
    return any(key == j for j in all_chk_values)


def int_round(num: int | float) -> int:
    if num - int(num) > int(num) + 1 - num:
        return int(num) + 1
    return int(num)
