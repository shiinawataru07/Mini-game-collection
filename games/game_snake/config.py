"""Configuration, themes, speed rules, and translations for Snake."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Color = tuple[int, int, int]
Language = Literal["en", "zh"]
Speed = Literal["slow", "normal", "fast"]

WINDOW_WIDTH = 820
WINDOW_HEIGHT = 700
MIN_WINDOW_WIDTH = 560
MIN_WINDOW_HEIGHT = 520
FPS = 60

GRID_WIDTH = 24
GRID_HEIGHT = 18
INITIAL_SNAKE_LENGTH = 4
FOOD_SCORE = 10

SPEEDS: dict[Speed, float] = {
    "slow": 5.0,
    "normal": 8.0,
    "fast": 12.0,
}
SPEED_ORDER: tuple[Speed, ...] = ("slow", "normal", "fast")

DEFAULT_THEME = "garden"
DEFAULT_LANGUAGE: Language = "zh"
DEFAULT_SPEED: Speed = "normal"


@dataclass(frozen=True)
class Theme:
    background: Color
    panel: Color
    board: Color
    grid: Color
    text: Color
    muted_text: Color
    snake_head: Color
    snake_body: Color
    snake_detail: Color
    food: Color
    food_detail: Color
    accent: Color
    overlay: Color


THEMES: dict[str, Theme] = {
    "garden": Theme(
        background=(241, 246, 235),
        panel=(255, 255, 249),
        board=(210, 226, 194),
        grid=(198, 216, 180),
        text=(49, 70, 45),
        muted_text=(105, 122, 97),
        snake_head=(63, 125, 68),
        snake_body=(91, 151, 83),
        snake_detail=(225, 242, 215),
        food=(218, 73, 65),
        food_detail=(72, 132, 67),
        accent=(231, 145, 65),
        overlay=(35, 53, 34),
    ),
    "night": Theme(
        background=(22, 29, 42),
        panel=(31, 41, 57),
        board=(42, 55, 68),
        grid=(50, 65, 78),
        text=(234, 241, 247),
        muted_text=(166, 180, 192),
        snake_head=(91, 211, 158),
        snake_body=(61, 178, 136),
        snake_detail=(225, 255, 244),
        food=(255, 104, 112),
        food_detail=(116, 220, 145),
        accent=(245, 188, 90),
        overlay=(11, 17, 27),
    ),
    "ocean": Theme(
        background=(232, 244, 249),
        panel=(250, 254, 255),
        board=(189, 220, 230),
        grid=(174, 208, 220),
        text=(39, 67, 79),
        muted_text=(92, 119, 130),
        snake_head=(32, 125, 149),
        snake_body=(54, 155, 174),
        snake_detail=(224, 250, 252),
        food=(239, 106, 76),
        food_detail=(54, 143, 101),
        accent=(48, 139, 187),
        overlay=(24, 51, 62),
    ),
}

THEME_ORDER = tuple(THEMES)

TEXTS: dict[Language, dict[str, str]] = {
    "en": {
        "title": "Snake",
        "score": "Score",
        "best": "Best",
        "speed": "Speed",
        "mode": "Mode",
        "back": "Menu",
        "pause": "Pause",
        "continue": "Continue",
        "restart": "Restart",
        "settings": "Settings",
        "settings_title": "Settings",
        "close": "Close",
        "theme": "Theme",
        "language": "Language",
        "slow": "Slow",
        "normal": "Normal",
        "fast": "Fast",
        "garden": "Garden",
        "night": "Night",
        "ocean": "Ocean",
        "english": "English",
        "chinese": "中文",
        "choose_mode": "Choose mode",
        "classic": "Classic",
        "classic_short": "Classic",
        "classic_desc": "Hitting a wall ends the game",
        "wrap": "Wrap-around",
        "wrap_short": "Wrap",
        "wrap_desc": "Exit one edge and enter the opposite edge",
        "ready": "Choose a direction to start",
        "paused": "Paused",
        "game_over": "Game Over",
        "won": "Board cleared!",
        "restart_hint": "Press R to play again",
        "hint": "Arrow keys / WASD move  ·  Space pauses  ·  Settings available while paused",
    },
    "zh": {
        "title": "贪吃蛇",
        "score": "分数",
        "best": "最佳",
        "speed": "速度",
        "mode": "模式",
        "back": "菜单",
        "pause": "暂停",
        "continue": "继续",
        "restart": "重开",
        "settings": "设置",
        "settings_title": "游戏设置",
        "close": "关闭",
        "theme": "主题",
        "language": "语言",
        "slow": "慢速",
        "normal": "中速",
        "fast": "快速",
        "garden": "花园",
        "night": "夜间",
        "ocean": "海洋",
        "english": "English",
        "chinese": "中文",
        "choose_mode": "选择游戏模式",
        "classic": "经典模式",
        "classic_short": "经典",
        "classic_desc": "碰到墙壁时游戏结束",
        "wrap": "里出外进模式",
        "wrap_short": "穿墙",
        "wrap_desc": "离开一侧后从相对一侧进入",
        "ready": "按方向键开始游戏",
        "paused": "游戏已暂停",
        "game_over": "游戏结束",
        "won": "恭喜占满棋盘！",
        "restart_hint": "按 R 再来一局",
        "hint": "方向键 / WASD 移动  ·  空格暂停  ·  暂停后可进入设置",
    },
}


def text(language: Language, key: str) -> str:
    return TEXTS[language][key]


def moves_per_second(speed: Speed) -> float:
    """Return the fixed simulation speed for one selected level."""

    try:
        return SPEEDS[speed]
    except KeyError as error:
        raise ValueError(f"Unsupported Snake speed: {speed}") from error


def move_interval_ms(speed: Speed) -> float:
    return 1000.0 / moves_per_second(speed)
