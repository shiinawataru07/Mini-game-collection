"""Best-time and player-preference persistence for Minesweeper."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .config import (
    DEFAULT_CUSTOM_SPEC,
    DEFAULT_DIFFICULTY,
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    DIFFICULTIES,
    DIFFICULTY_ORDER,
    TEXTS,
    THEMES,
    Difficulty,
    Language,
    PresetDifficulty,
    normalize_custom_spec,
)

PLAYER_DATA_PATH = Path(__file__).with_name(".player_data.json")


def _default_best_times() -> dict[PresetDifficulty, int | None]:
    return {difficulty: None for difficulty in DIFFICULTIES}


@dataclass(frozen=True)
class PlayerData:
    best_times_ms: dict[PresetDifficulty, int | None] = field(default_factory=_default_best_times)
    theme: str = DEFAULT_THEME
    language: Language = DEFAULT_LANGUAGE
    difficulty: Difficulty = DEFAULT_DIFFICULTY
    custom_width: int = DEFAULT_CUSTOM_SPEC.width
    custom_height: int = DEFAULT_CUSTOM_SPEC.height
    custom_mines: int = DEFAULT_CUSTOM_SPEC.mines


def load_player_data(path: Path = PLAYER_DATA_PATH) -> PlayerData:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_times = payload.get("best_times_ms", {})
        times = _default_best_times()
        if isinstance(raw_times, dict):
            for difficulty in DIFFICULTIES:
                value = raw_times.get(difficulty)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    times[difficulty] = value
        theme = payload.get("theme", DEFAULT_THEME)
        language = payload.get("language", DEFAULT_LANGUAGE)
        difficulty = payload.get("difficulty", DEFAULT_DIFFICULTY)
        if theme not in THEMES:
            theme = DEFAULT_THEME
        if language not in TEXTS:
            language = DEFAULT_LANGUAGE
        if difficulty not in DIFFICULTY_ORDER:
            difficulty = DEFAULT_DIFFICULTY
        custom = normalize_custom_spec(
            payload.get("custom_width"),
            payload.get("custom_height"),
            payload.get("custom_mines"),
        )
        return PlayerData(
            times,
            theme,
            language,
            difficulty,
            custom.width,
            custom.height,
            custom.mines,
        )
    except (OSError, json.JSONDecodeError, AttributeError, TypeError):
        return PlayerData()


def update_best_time(data: PlayerData, difficulty: PresetDifficulty, elapsed_ms: int) -> PlayerData:
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"Unsupported Minesweeper difficulty: {difficulty}")
    if elapsed_ms < 0:
        raise ValueError("Best time must not be negative.")
    current = data.best_times_ms[difficulty]
    if current is not None and current <= elapsed_ms:
        return data
    times = dict(data.best_times_ms)
    times[difficulty] = elapsed_ms
    return PlayerData(
        times,
        data.theme,
        data.language,
        data.difficulty,
        data.custom_width,
        data.custom_height,
        data.custom_mines,
    )


def save_player_data(data: PlayerData, path: Path = PLAYER_DATA_PATH) -> bool:
    if (
        data.theme not in THEMES
        or data.language not in TEXTS
        or data.difficulty not in DIFFICULTY_ORDER
    ):
        return False
    custom = normalize_custom_spec(data.custom_width, data.custom_height, data.custom_mines)
    if (data.custom_width, data.custom_height, data.custom_mines) != (
        custom.width,
        custom.height,
        custom.mines,
    ):
        return False
    times: dict[str, int | None] = {}
    for difficulty in DIFFICULTIES:
        value = data.best_times_ms.get(difficulty)
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 0
        ):
            return False
        times[difficulty] = value
    payload = {
        "best_times_ms": times,
        "theme": data.theme,
        "language": data.language,
        "difficulty": data.difficulty,
        "custom_width": data.custom_width,
        "custom_height": data.custom_height,
        "custom_mines": data.custom_mines,
    }
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False
