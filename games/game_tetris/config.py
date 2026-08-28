"""Configuration, themes, scoring, and translations for Tetris."""

from __future__ import annotations

from dataclasses import dataclass

from games.common.i18n import bind_translations
from games.common.types import Color, Language

WINDOW_WIDTH = 760
WINDOW_HEIGHT = 780
MIN_WINDOW_WIDTH = 560
MIN_WINDOW_HEIGHT = 640
FPS = 60

BOARD_WIDTH = 10
VISIBLE_HEIGHT = 20
HIDDEN_ROWS = 2
BOARD_HEIGHT = VISIBLE_HEIGHT + HIDDEN_ROWS
NEXT_COUNT = 5

LOCK_DELAY_MS = 500
MAX_LOCK_RESETS = 15
DAS_MS = 160
ARR_MS = 45
LINE_CLEAR_ANIMATION_MS = 180
SPRINT_TARGET_LINES = 40
TIMED_MODE_MS = 120_000

DEFAULT_THEME = "midnight"
DEFAULT_LANGUAGE: Language = "zh"


@dataclass(frozen=True)
class Theme:
    background: Color
    panel: Color
    board: Color
    grid: Color
    text: Color
    muted_text: Color
    accent: Color
    ghost: Color
    pieces: tuple[Color, ...]


THEMES: dict[str, Theme] = {
    "midnight": Theme(
        background=(19, 23, 38),
        panel=(30, 36, 56),
        board=(10, 13, 24),
        grid=(35, 42, 63),
        text=(239, 243, 255),
        muted_text=(151, 161, 190),
        accent=(139, 116, 255),
        ghost=(111, 121, 153),
        pieces=(
            (0, 0, 0),
            (42, 212, 226),
            (246, 211, 66),
            (172, 91, 235),
            (83, 209, 104),
            (239, 75, 91),
            (69, 116, 232),
            (244, 151, 55),
        ),
    ),
    "light": Theme(
        background=(239, 243, 249),
        panel=(255, 255, 255),
        board=(219, 226, 238),
        grid=(196, 206, 222),
        text=(42, 49, 66),
        muted_text=(99, 110, 133),
        accent=(95, 78, 208),
        ghost=(145, 154, 174),
        pieces=(
            (0, 0, 0),
            (13, 174, 194),
            (225, 178, 22),
            (146, 67, 202),
            (46, 173, 73),
            (215, 57, 73),
            (51, 91, 205),
            (224, 123, 29),
        ),
    ),
    "classic": Theme(
        background=(25, 42, 46),
        panel=(38, 59, 63),
        board=(14, 28, 31),
        grid=(49, 70, 73),
        text=(244, 241, 224),
        muted_text=(166, 177, 164),
        accent=(237, 196, 71),
        ghost=(118, 137, 131),
        pieces=(
            (0, 0, 0),
            (45, 196, 204),
            (239, 209, 68),
            (176, 94, 204),
            (91, 184, 92),
            (220, 78, 75),
            (71, 108, 204),
            (225, 139, 55),
        ),
    ),
}

TEXTS: dict[Language, dict[str, str]] = {
    "en": {
        "back": "Back",
        "pause": "Pause",
        "resume": "Resume",
        "restart": "Restart",
        "settings": "Settings",
        "score": "Score",
        "best": "Best",
        "lines": "Lines",
        "level": "Level",
        "time": "Time",
        "best_time": "Best time",
        "target": "Target",
        "choose_mode": "Choose a mode",
        "choose_mode_hint": "Press 1 / 2 / 3 or click a card · Tab changes mode",
        "marathon": "Marathon",
        "marathon_desc": "Classic endless play · level up every 10 lines",
        "sprint": "Sprint",
        "sprint_desc": "Clear 40 lines as quickly as possible",
        "timed": "Timed",
        "timed_desc": "Score as much as possible in 2 minutes",
        "sprint_complete": "Sprint Complete!",
        "timed_complete": "Time's Up!",
        "change_mode_hint": "R restarts · Tab changes mode",
        "hold": "HOLD",
        "next": "NEXT",
        "paused": "Paused",
        "game_over": "Game Over",
        "restart_hint": "Press R to restart",
        "theme": "Color theme",
        "language": "Language",
        "midnight": "Midnight",
        "light": "Light",
        "classic": "Classic",
        "english": "English",
        "chinese": "中文",
        "close": "Close",
        "hint": "Arrows/WASD move · Z/X rotate · Space hard drop · C hold · P pause · Tab mode",
    },
    "zh": {
        "back": "返回",
        "pause": "暂停",
        "resume": "继续",
        "restart": "重开",
        "settings": "设置",
        "score": "分数",
        "best": "最高分",
        "lines": "消行",
        "level": "等级",
        "time": "时间",
        "best_time": "最佳时间",
        "target": "目标",
        "choose_mode": "选择游戏模式",
        "choose_mode_hint": "按 1 / 2 / 3 或点击卡片 · Tab 可切换模式",
        "marathon": "马拉松",
        "marathon_desc": "经典无尽玩法 · 每 10 行提升等级",
        "sprint": "冲刺",
        "sprint_desc": "以最快速度消除 40 行",
        "timed": "计时",
        "timed_desc": "在 2 分钟内争取最高分",
        "sprint_complete": "冲刺完成！",
        "timed_complete": "时间到！",
        "change_mode_hint": "R 再来一局 · Tab 切换模式",
        "hold": "暂存",
        "next": "下一个",
        "paused": "已暂停",
        "game_over": "游戏结束",
        "restart_hint": "按 R 重新开始",
        "theme": "颜色主题",
        "language": "语言",
        "midnight": "午夜",
        "light": "明亮",
        "classic": "经典",
        "english": "English",
        "chinese": "中文",
        "close": "关闭",
        "hint": "方向键/WASD 移动 · Z/X 旋转 · 空格硬降 · C 暂存 · P 暂停 · Tab 模式",
    },
}


text = bind_translations(TEXTS)


def gravity_interval_ms(level: int) -> float:
    """Return a smooth, bounded gravity interval for the selected level."""

    return max(55.0, 800.0 * 0.82 ** max(0, level - 1))
