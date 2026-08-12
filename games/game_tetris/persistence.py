"""Local records and preferences for Tetris."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from games.common.json_store import (
    choice_or_default,
    load_json_object,
    non_negative_int,
    save_json_object,
)

from .config import DEFAULT_LANGUAGE, DEFAULT_THEME, TEXTS, THEMES, Language

PLAYER_DATA_PATH = Path(__file__).with_name(".player_data.json")


@dataclass(frozen=True)
class PlayerData:
    best_score: int = 0
    best_lines: int = 0
    theme: str = DEFAULT_THEME
    language: Language = DEFAULT_LANGUAGE


def load_player_data(path: Path = PLAYER_DATA_PATH) -> PlayerData:
    payload = load_json_object(path)
    if payload is None:
        return PlayerData()
    return PlayerData(
        non_negative_int(payload.get("best_score")),
        non_negative_int(payload.get("best_lines")),
        choice_or_default(payload.get("theme"), THEMES, DEFAULT_THEME),
        choice_or_default(payload.get("language"), TEXTS, DEFAULT_LANGUAGE),
    )


def save_player_data(data: PlayerData, path: Path = PLAYER_DATA_PATH) -> bool:
    if data.theme not in THEMES or data.language not in TEXTS:
        return False
    payload = {
        "best_score": max(0, data.best_score),
        "best_lines": max(0, data.best_lines),
        "theme": data.theme,
        "language": data.language,
    }
    return save_json_object(path, payload)
