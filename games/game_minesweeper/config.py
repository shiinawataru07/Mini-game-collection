"""Configuration, themes, difficulties, and translations for Minesweeper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Color = tuple[int, int, int]
Language = Literal["en", "zh"]
Difficulty = Literal["beginner", "intermediate", "expert"]

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
MIN_WINDOW_WIDTH = 640
MIN_WINDOW_HEIGHT = 520
FPS = 60
HINT_DISPLAY_MS = 4000

DEFAULT_THEME = "classic"
DEFAULT_LANGUAGE: Language = "zh"
DEFAULT_DIFFICULTY: Difficulty = "beginner"


@dataclass(frozen=True)
class DifficultySpec:
    width: int
    height: int
    mines: int


DIFFICULTIES: dict[Difficulty, DifficultySpec] = {
    "beginner": DifficultySpec(9, 9, 10),
    "intermediate": DifficultySpec(16, 16, 40),
    "expert": DifficultySpec(30, 16, 99),
}
DIFFICULTY_ORDER: tuple[Difficulty, ...] = ("beginner", "intermediate", "expert")


@dataclass(frozen=True)
class Theme:
    background: Color
    panel: Color
    board_border: Color
    hidden_cell: Color
    hidden_highlight: Color
    revealed_cell: Color
    grid: Color
    text: Color
    muted_text: Color
    accent: Color
    flag: Color
    mine: Color
    danger: Color
    overlay: Color


THEMES: dict[str, Theme] = {
    "classic": Theme(
        background=(238, 241, 245),
        panel=(255, 255, 255),
        board_border=(116, 129, 145),
        hidden_cell=(177, 188, 201),
        hidden_highlight=(218, 225, 232),
        revealed_cell=(229, 233, 238),
        grid=(153, 164, 177),
        text=(42, 50, 61),
        muted_text=(103, 113, 126),
        accent=(49, 110, 184),
        flag=(218, 67, 62),
        mine=(42, 47, 54),
        danger=(224, 76, 70),
        overlay=(31, 38, 48),
    ),
    "forest": Theme(
        background=(238, 245, 237),
        panel=(253, 255, 250),
        board_border=(89, 116, 88),
        hidden_cell=(151, 181, 145),
        hidden_highlight=(205, 224, 199),
        revealed_cell=(225, 235, 220),
        grid=(130, 158, 126),
        text=(42, 66, 43),
        muted_text=(93, 116, 91),
        accent=(64, 133, 76),
        flag=(218, 93, 55),
        mine=(48, 61, 46),
        danger=(213, 75, 61),
        overlay=(29, 48, 30),
    ),
    "night": Theme(
        background=(23, 29, 40),
        panel=(34, 43, 58),
        board_border=(105, 121, 143),
        hidden_cell=(70, 87, 108),
        hidden_highlight=(111, 130, 153),
        revealed_cell=(48, 60, 76),
        grid=(82, 98, 119),
        text=(235, 241, 247),
        muted_text=(165, 178, 194),
        accent=(91, 167, 235),
        flag=(255, 112, 102),
        mine=(228, 235, 242),
        danger=(206, 70, 75),
        overlay=(10, 14, 22),
    ),
}
THEME_ORDER = tuple(THEMES)

NUMBER_COLORS: dict[int, Color] = {
    1: (42, 101, 190),
    2: (51, 128, 72),
    3: (205, 67, 57),
    4: (83, 65, 153),
    5: (145, 72, 50),
    6: (30, 134, 140),
    7: (49, 54, 61),
    8: (113, 121, 132),
}

TEXTS: dict[Language, dict[str, str]] = {
    "en": {
        "title": "Minesweeper",
        "back": "Menu",
        "settings": "Settings",
        "restart": "Restart",
        "get_hint": "Hint",
        "mines": "Mines",
        "time": "Time",
        "best": "Best",
        "difficulty": "Difficulty",
        "beginner": "Beginner",
        "intermediate": "Intermediate",
        "expert": "Expert",
        "theme": "Theme",
        "classic": "Classic",
        "forest": "Forest",
        "night": "Night",
        "language": "Language",
        "english": "English",
        "chinese": "中文",
        "settings_title": "Game settings",
        "close": "Close",
        "ready": "Reveal any cell to start",
        "won": "Board cleared!",
        "lost": "Mine triggered",
        "restart_hint": "Press R to play again",
        "hint": "Left click reveals  ·  Right click cycles flag / ?  ·  Click a number to clear",
        "hint_safe": "Hint: this cell is logically safe",
        "hint_mine": "Hint: this cell must contain a mine",
        "hint_incorrect_flag": "Hint: this flag is incorrect",
        "hint_none": "No logical hint is available; check your flags",
        "no_record": "--",
    },
    "zh": {
        "title": "扫雷",
        "back": "菜单",
        "settings": "设置",
        "restart": "重开",
        "get_hint": "提示",
        "mines": "剩余雷数",
        "time": "时间",
        "best": "最佳",
        "difficulty": "难度",
        "beginner": "初级",
        "intermediate": "中级",
        "expert": "高级",
        "theme": "主题",
        "classic": "经典",
        "forest": "森林",
        "night": "夜间",
        "language": "语言",
        "english": "English",
        "chinese": "中文",
        "settings_title": "游戏设置",
        "close": "关闭",
        "ready": "点击任意格子开始",
        "won": "排雷成功！",
        "lost": "踩到地雷了",
        "restart_hint": "按 R 再来一局",
        "hint": "左键翻开  ·  右键循环旗帜 / 问号  ·  点击数字可展开周围格子",
        "hint_safe": "提示：这个格子通过逻辑可确定安全",
        "hint_mine": "提示：这个格子通过逻辑可确定有雷",
        "hint_incorrect_flag": "提示：这个旗帜标记错误",
        "hint_none": "当前没有可用逻辑提示，请检查旗帜",
        "no_record": "--",
    },
}


def text(language: Language, key: str) -> str:
    return TEXTS[language][key]
