"""Local best-score and preference persistence for Snake."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import (
    DEFAULT_LANGUAGE,
    DEFAULT_SPEED,
    DEFAULT_THEME,
    SPEEDS,
    TEXTS,
    THEMES,
    Speed,
)

PLAYER_DATA_PATH = Path(__file__).with_name(".player_data.json")


@dataclass(frozen=True)
class PlayerData:
    best_score: int = 0
    theme: str = DEFAULT_THEME
    language: str = DEFAULT_LANGUAGE
    speed: Speed = DEFAULT_SPEED


def load_player_data(path: Path = PLAYER_DATA_PATH) -> PlayerData:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        score = payload.get("best_score", 0)
        theme = payload.get("theme", DEFAULT_THEME)
        language = payload.get("language", DEFAULT_LANGUAGE)
        speed = payload.get("speed", DEFAULT_SPEED)
        if not isinstance(score, int) or isinstance(score, bool) or score < 0:
            score = 0
        if theme not in THEMES:
            theme = DEFAULT_THEME
        if language not in TEXTS:
            language = DEFAULT_LANGUAGE
        if speed not in SPEEDS:
            speed = DEFAULT_SPEED
        return PlayerData(score, theme, language, speed)
    except (OSError, json.JSONDecodeError, AttributeError, TypeError):
        return PlayerData()


def save_player_data(
    best_score: int,
    theme: str,
    language: str,
    path: Path = PLAYER_DATA_PATH,
    speed: Speed = DEFAULT_SPEED,
) -> bool:
    if theme not in THEMES or language not in TEXTS or speed not in SPEEDS:
        return False
    payload = {
        "best_score": max(0, best_score),
        "theme": theme,
        "language": language,
        "speed": speed,
    }
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False
