"""Shared configuration, themes, and translations for 2048."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Color = tuple[int, int, int]
Language = Literal["en", "zh"]
AiSpeed = Literal["slow", "normal", "fast"]

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 620
MIN_WINDOW_WIDTH = 360
MIN_WINDOW_HEIGHT = 500
FPS = 60

SLIDE_ANIMATION_MS = 100
TILE_EFFECT_ANIMATION_MS = 90
TOTAL_MOVE_ANIMATION_MS = SLIDE_ANIMATION_MS + TILE_EFFECT_ANIMATION_MS
SCORE_POPUP_MS = 650
AI_SEARCH_DEPTH = 3
AI_MOVE_DELAYS: dict[AiSpeed, int] = {
    "slow": 600,
    "normal": 280,
    "fast": 40,
}
AI_SPEED_ORDER: tuple[AiSpeed, ...] = ("slow", "normal", "fast")

DEFAULT_THEME = "warm"
DEFAULT_LANGUAGE: Language = "en"
DEFAULT_AI_SPEED: AiSpeed = "normal"


@dataclass(frozen=True)
class Theme:
    """Colors used to render one visual theme."""

    background: Color
    board: Color
    empty_cell: Color
    text: Color
    light_text: Color
    accent: Color
    tiles: dict[int, Color]


THEMES: dict[str, Theme] = {
    "warm": Theme(
        background=(250, 248, 239),
        board=(187, 173, 160),
        empty_cell=(205, 193, 180),
        text=(119, 110, 101),
        light_text=(249, 246, 242),
        accent=(143, 122, 102),
        tiles={
            2: (238, 228, 218),
            4: (237, 224, 200),
            8: (242, 177, 121),
            16: (245, 149, 99),
            32: (246, 124, 95),
            64: (246, 94, 59),
            128: (237, 207, 114),
            256: (237, 204, 97),
            512: (237, 200, 80),
            1024: (237, 197, 63),
            2048: (237, 194, 46),
        },
    ),
    "blue": Theme(
        background=(241, 247, 252),
        board=(156, 180, 201),
        empty_cell=(202, 217, 229),
        text=(61, 79, 94),
        light_text=(247, 251, 255),
        accent=(74, 139, 193),
        tiles={
            2: (222, 237, 247),
            4: (203, 227, 243),
            8: (163, 210, 239),
            16: (121, 190, 232),
            32: (83, 169, 222),
            64: (50, 146, 207),
            128: (96, 173, 196),
            256: (73, 154, 181),
            512: (53, 134, 164),
            1024: (37, 113, 143),
            2048: (24, 92, 122),
        },
    ),
    "green": Theme(
        background=(243, 249, 243),
        board=(157, 184, 160),
        empty_cell=(207, 222, 207),
        text=(60, 83, 62),
        light_text=(248, 252, 248),
        accent=(82, 145, 91),
        tiles={
            2: (225, 239, 225),
            4: (208, 232, 209),
            8: (174, 216, 177),
            16: (139, 198, 145),
            32: (105, 180, 113),
            64: (76, 159, 86),
            128: (129, 184, 126),
            256: (105, 163, 104),
            512: (82, 143, 84),
            1024: (61, 122, 66),
            2048: (43, 101, 50),
        },
    ),
}

TEXTS: dict[Language, dict[str, str]] = {
    "en": {
        "settings": "Settings",
        "score": "Score",
        "hint": "Arrow keys / WASD to move   R to restart",
        "game_over": "Game Over",
        "restart_hint": "Press R to restart",
        "color_theme": "Color theme",
        "language": "Language",
        "warm": "Warm",
        "blue": "Light Blue",
        "green": "Light Green",
        "english": "English",
        "chinese": "中文",
        "restart": "Restart game",
        "best_score": "Best score",
        "copy_save": "Copy save JSON",
        "load_save": "Load JSON",
        "save_copied": "Save JSON copied to clipboard",
        "load_success": "Save loaded successfully",
        "invalid_save": "Invalid save JSON",
        "clipboard_error": "Clipboard is unavailable",
        "ai_player": "AI player",
        "start_ai": "Start AI",
        "pause_ai": "Pause AI",
        "ai_speed": "Speed: {speed}",
        "slow": "Slow",
        "normal": "Normal",
        "fast": "Fast",
    },
    "zh": {
        "settings": "设置",
        "score": "分数",
        "hint": "方向键 / WASD 移动    R 重新开始",
        "game_over": "游戏结束",
        "restart_hint": "按 R 重新开始",
        "color_theme": "颜色主题",
        "language": "语言",
        "warm": "暖橙色",
        "blue": "淡蓝色",
        "green": "淡绿色",
        "english": "English",
        "chinese": "中文",
        "restart": "重新开始游戏",
        "best_score": "历史最佳分数",
        "copy_save": "复制存档 JSON",
        "load_save": "读取 JSON",
        "save_copied": "存档 JSON 已复制到剪贴板",
        "load_success": "读档成功",
        "invalid_save": "存档 JSON 无效",
        "clipboard_error": "无法访问剪贴板",
        "ai_player": "AI 自动游玩",
        "start_ai": "启动 AI",
        "pause_ai": "暂停 AI",
        "ai_speed": "速度：{speed}",
        "slow": "慢速",
        "normal": "标准",
        "fast": "快速",
    },
}


def text(language: Language, key: str) -> str:
    """Return translated UI text."""

    return TEXTS[language][key]
