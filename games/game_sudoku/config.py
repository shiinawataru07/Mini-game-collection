"""Configuration, themes, and translations for Sudoku."""

from __future__ import annotations

from dataclasses import dataclass

from games.common.i18n import bind_translations
from games.common.types import Color, Language

WINDOW_WIDTH = 820
WINDOW_HEIGHT = 850
MIN_WINDOW_WIDTH = 620
MIN_WINDOW_HEIGHT = 720
FPS = 60

DEFAULT_THEME = "paper"
DEFAULT_LANGUAGE: Language = "zh"


@dataclass(frozen=True)
class Theme:
    background: Color
    panel: Color
    board: Color
    alternate: Color
    selected: Color
    related: Color
    grid: Color
    box_grid: Color
    text: Color
    muted_text: Color
    given: Color
    entry: Color
    accent: Color
    note: Color
    error: Color
    success: Color
    overlay: Color


THEMES: dict[str, Theme] = {
    "paper": Theme(
        (239, 242, 237),
        (255, 255, 252),
        (255, 255, 255),
        (246, 248, 244),
        (205, 229, 222),
        (231, 241, 237),
        (190, 201, 195),
        (65, 82, 77),
        (43, 54, 51),
        (112, 126, 120),
        (37, 48, 45),
        (37, 122, 137),
        (47, 139, 126),
        (100, 126, 129),
        (200, 69, 73),
        (54, 151, 104),
        (21, 31, 29),
    ),
    "night": Theme(
        (18, 24, 31),
        (29, 38, 48),
        (24, 31, 40),
        (28, 37, 47),
        (47, 83, 88),
        (35, 54, 61),
        (62, 75, 87),
        (159, 190, 188),
        (235, 242, 242),
        (146, 160, 169),
        (232, 237, 239),
        (87, 202, 212),
        (76, 191, 179),
        (130, 155, 164),
        (244, 111, 117),
        (95, 207, 145),
        (4, 7, 10),
    ),
    "sakura": Theme(
        (250, 241, 242),
        (255, 251, 250),
        (255, 254, 253),
        (252, 246, 246),
        (246, 211, 218),
        (250, 231, 235),
        (220, 195, 200),
        (105, 69, 78),
        (74, 51, 57),
        (137, 108, 115),
        (66, 47, 51),
        (178, 74, 103),
        (197, 92, 121),
        (145, 112, 120),
        (205, 65, 75),
        (80, 153, 108),
        (46, 26, 31),
    ),
}

TEXTS: dict[Language, dict[str, str]] = {
    "en": {
        "title": "Sudoku",
        "back": "Menu",
        "levels": "Levels",
        "settings": "Settings",
        "restart": "Restart",
        "difficulty": "Difficulty",
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
        "level": "Level",
        "time": "Time",
        "mistakes": "Mistakes",
        "hints": "Hints",
        "note": "Notes",
        "hint_button": "Hint",
        "undo": "Undo",
        "redo": "Redo",
        "erase": "Erase",
        "pause": "Pause",
        "resume": "Resume",
        "paused": "Paused",
        "won": "Puzzle Complete!",
        "won_hint": "R replay · L choose another level",
        "choose_level": "Choose a level",
        "completed": "Completed",
        "best": "Best",
        "close": "Close",
        "theme": "Theme",
        "language": "Language",
        "paper": "Paper",
        "night": "Night",
        "sakura": "Sakura",
        "english": "English",
        "chinese": "中文",
        "settings_title": "Sudoku settings",
        "hint": "Click or arrows select · 1–9 fill · N notes · H hint · Ctrl+Z/Y undo/redo",
    },
    "zh": {
        "title": "数独",
        "back": "菜单",
        "levels": "关卡",
        "settings": "设置",
        "restart": "重开",
        "difficulty": "难度",
        "easy": "简单",
        "medium": "中等",
        "hard": "困难",
        "level": "关卡",
        "time": "用时",
        "mistakes": "错误",
        "hints": "提示",
        "note": "笔记",
        "hint_button": "提示",
        "undo": "撤销",
        "redo": "重做",
        "erase": "清除",
        "pause": "暂停",
        "resume": "继续",
        "paused": "已暂停",
        "won": "恭喜完成！",
        "won_hint": "R 再玩一次 · L 选择其他关卡",
        "choose_level": "选择关卡",
        "completed": "已完成",
        "best": "最佳",
        "close": "关闭",
        "theme": "主题",
        "language": "语言",
        "paper": "纸张",
        "night": "夜间",
        "sakura": "樱花",
        "english": "English",
        "chinese": "中文",
        "settings_title": "数独设置",
        "hint": "点击或方向键选格 · 1–9 填数 · N 笔记 · H 提示 · Ctrl+Z/Y 撤销重做",
    },
}

text = bind_translations(TEXTS)
