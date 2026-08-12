"""JSON saves and local best-score persistence for 2048."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from games.common.json_store import (
    is_non_negative_int,
    load_json_object,
    save_json_object,
)

from .logic import SUPPORTED_BOARD_SIZES, Board, GameState, can_move

SAVE_VERSION = 1
PLAYER_DATA_PATH = Path(__file__).with_name(".player_data.json")


@dataclass(frozen=True)
class SavedGame:
    """A validated game state and its saved preferences."""

    state: GameState
    best_score: int
    theme: str
    language: str


def create_save_json(
    state: GameState,
    best_score: int,
    theme: str,
    language: str,
) -> str:
    """Serialize the current game and preferences as portable JSON text."""

    payload = {
        "format": "mini-game-collection",
        "version": SAVE_VERSION,
        "game": "2048",
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "state": {
            "board": state.board,
            "score": state.score,
            "game_over": state.game_over,
        },
        "best_score": max(best_score, state.score),
        "preferences": {"theme": theme, "language": language},
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _validate_saved_board(board) -> Board:
    if not isinstance(board, list) or len(board) not in SUPPORTED_BOARD_SIZES:
        raise ValueError("The save must contain a supported square board.")

    size = len(board)
    validated: Board = []
    for row in board:
        if not isinstance(row, list) or len(row) != size:
            raise ValueError("The save must contain a supported square board.")

        validated_row: list[int] = []
        for value in row:
            is_tile = is_non_negative_int(value) and (
                value == 0 or (value >= 2 and value & (value - 1) == 0)
            )
            if not is_tile:
                raise ValueError("Board tiles must be zero or powers of two.")
            validated_row.append(value)
        validated.append(validated_row)
    return validated


def parse_save_json(
    value: str,
    allowed_themes: set[str] | None = None,
    allowed_languages: set[str] | None = None,
) -> SavedGame:
    """Parse and strictly validate JSON save text."""

    try:
        payload = json.loads(value)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError("The clipboard does not contain valid JSON.") from error

    if not isinstance(payload, dict):
        raise ValueError("The save JSON must contain an object.")
    if payload.get("format") != "mini-game-collection":
        raise ValueError("This is not a Mini Game Collection save.")
    if payload.get("version") != SAVE_VERSION:
        raise ValueError("This save version is not supported.")
    if payload.get("game") != "2048":
        raise ValueError("This save is not for 2048.")

    raw_state = payload.get("state")
    if not isinstance(raw_state, dict):
        raise ValueError("The save does not contain a game state.")

    board = _validate_saved_board(raw_state.get("board"))
    score = raw_state.get("score")
    saved_game_over = raw_state.get("game_over")
    if not is_non_negative_int(score):
        raise ValueError("The saved score must be a non-negative integer.")
    if not isinstance(saved_game_over, bool):
        raise ValueError("The saved game-over value must be true or false.")

    calculated_game_over = not can_move(board)
    if saved_game_over != calculated_game_over:
        raise ValueError("The saved game-over value does not match the board.")

    best_score = payload.get("best_score")
    if not is_non_negative_int(best_score):
        raise ValueError("The saved best score must be a non-negative integer.")

    preferences = payload.get("preferences")
    if not isinstance(preferences, dict):
        raise ValueError("The save does not contain preferences.")
    theme = preferences.get("theme")
    language = preferences.get("language")
    if not isinstance(theme, str) or (allowed_themes is not None and theme not in allowed_themes):
        raise ValueError("The saved theme is not supported.")
    if not isinstance(language, str) or (
        allowed_languages is not None and language not in allowed_languages
    ):
        raise ValueError("The saved language is not supported.")

    return SavedGame(
        state=GameState(board=board, score=score, game_over=calculated_game_over),
        best_score=max(best_score, score),
        theme=theme,
        language=language,
    )


def load_best_score(path: Path = PLAYER_DATA_PATH) -> int:
    """Load the locally persisted best score, returning zero if unavailable."""

    payload = load_json_object(path)
    if payload is not None:
        score = payload.get("best_score")
        if is_non_negative_int(score):
            return score
    return 0


def save_best_score(score: int, path: Path = PLAYER_DATA_PATH) -> bool:
    """Persist the best score without interrupting the game on I/O errors."""

    return save_json_object(path, {"best_score": max(0, score)}, ensure_ascii=True)
