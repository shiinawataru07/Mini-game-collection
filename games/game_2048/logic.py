"""Core rules for 2048, independent from Pygame."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

Board = list[list[int]]
Direction = Literal["up", "down", "left", "right"]

BOARD_SIZE = 4
NEW_TILE_FOUR_CHANCE = 0.1
SAVE_VERSION = 1


@dataclass
class GameState:
    """Everything needed to describe one 2048 game."""

    board: Board
    score: int = 0
    game_over: bool = False


@dataclass(frozen=True)
class SavedGame:
    """A validated game state and its saved preferences."""

    state: GameState
    best_score: int
    theme: str
    language: str


def create_empty_board(size: int = BOARD_SIZE) -> Board:
    """Create a square board filled with zeroes."""

    return [[0 for _ in range(size)] for _ in range(size)]


def merge_line(line: list[int]) -> tuple[list[int], int]:
    """Slide and merge one row to the left.

    Returns the merged row and the score earned by this merge.
    """

    non_zero = [value for value in line if value != 0]
    merged: list[int] = []
    score = 0
    index = 0

    while index < len(non_zero):
        if index + 1 < len(non_zero) and non_zero[index] == non_zero[index + 1]:
            value = non_zero[index] * 2
            merged.append(value)
            score += value
            index += 2
        else:
            merged.append(non_zero[index])
            index += 1

    merged.extend([0] * (len(line) - len(merged)))
    return merged, score


def _transpose(board: Board) -> Board:
    return [list(column) for column in zip(*board)]


def _move_left(board: Board) -> tuple[Board, int]:
    moved_board: Board = []
    score = 0

    for row in board:
        moved_row, row_score = merge_line(row)
        moved_board.append(moved_row)
        score += row_score

    return moved_board, score


def _move_right(board: Board) -> tuple[Board, int]:
    reversed_board = [list(reversed(row)) for row in board]
    moved_board, score = _move_left(reversed_board)
    return [list(reversed(row)) for row in moved_board], score


def move_board(board: Board, direction: Direction) -> tuple[Board, int, bool]:
    """Move an entire board and report its score and whether it changed."""

    if direction == "left":
        moved_board, score = _move_left(board)
    elif direction == "right":
        moved_board, score = _move_right(board)
    elif direction == "up":
        moved_columns, score = _move_left(_transpose(board))
        moved_board = _transpose(moved_columns)
    elif direction == "down":
        moved_columns, score = _move_right(_transpose(board))
        moved_board = _transpose(moved_columns)
    else:
        raise ValueError(f"Unsupported direction: {direction}")

    return moved_board, score, moved_board != board


def empty_cells(board: Board) -> list[tuple[int, int]]:
    """Return all empty cell coordinates in row-major order."""

    return [
        (row_index, column_index)
        for row_index, row in enumerate(board)
        for column_index, value in enumerate(row)
        if value == 0
    ]


def add_random_tile(board: Board, rng=None) -> Board:
    """Return a board with one new 2 or 4 in a random empty cell."""

    rng = rng or random
    result = [row[:] for row in board]
    available = empty_cells(result)
    if not available:
        return result

    row, column = rng.choice(available)
    result[row][column] = 4 if rng.random() < NEW_TILE_FOUR_CHANCE else 2
    return result


def can_move(board: Board) -> bool:
    """Return whether at least one legal move remains."""

    if empty_cells(board):
        return True

    size = len(board)
    for row in range(size):
        for column in range(size):
            value = board[row][column]
            if column + 1 < size and value == board[row][column + 1]:
                return True
            if row + 1 < size and value == board[row + 1][column]:
                return True

    return False


def new_game(size: int = BOARD_SIZE, rng=None) -> GameState:
    """Create a fresh game with two starting tiles."""

    board = create_empty_board(size)
    board = add_random_tile(board, rng)
    board = add_random_tile(board, rng)
    return GameState(board=board)


def apply_move(state: GameState, direction: Direction, rng=None) -> GameState:
    """Apply one player move and return the resulting state."""

    if state.game_over:
        return state

    moved_board, gained_score, changed = move_board(state.board, direction)
    if changed:
        moved_board = add_random_tile(moved_board, rng)

    return GameState(
        board=moved_board,
        score=state.score + gained_score,
        game_over=not can_move(moved_board),
    )


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
        "preferences": {
            "theme": theme,
            "language": language,
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _is_non_negative_integer(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_saved_board(board) -> Board:
    if not isinstance(board, list) or len(board) != BOARD_SIZE:
        raise ValueError("The save must contain a 4x4 board.")

    validated: Board = []
    for row in board:
        if not isinstance(row, list) or len(row) != BOARD_SIZE:
            raise ValueError("The save must contain a 4x4 board.")

        validated_row: list[int] = []
        for value in row:
            is_tile = _is_non_negative_integer(value) and (
                value == 0 or (value >= 2 and value & (value - 1) == 0)
            )
            if not is_tile:
                raise ValueError("Board tiles must be zero or powers of two.")
            validated_row.append(value)
        validated.append(validated_row)

    return validated


def parse_save_json(
    text: str,
    allowed_themes: set[str] | None = None,
    allowed_languages: set[str] | None = None,
) -> SavedGame:
    """Parse and strictly validate JSON save text."""

    try:
        payload = json.loads(text)
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
    if not _is_non_negative_integer(score):
        raise ValueError("The saved score must be a non-negative integer.")
    if not isinstance(saved_game_over, bool):
        raise ValueError("The saved game-over value must be true or false.")

    calculated_game_over = not can_move(board)
    if saved_game_over != calculated_game_over:
        raise ValueError("The saved game-over value does not match the board.")

    best_score = payload.get("best_score")
    if not _is_non_negative_integer(best_score):
        raise ValueError("The saved best score must be a non-negative integer.")

    preferences = payload.get("preferences")
    if not isinstance(preferences, dict):
        raise ValueError("The save does not contain preferences.")
    theme = preferences.get("theme")
    language = preferences.get("language")
    if not isinstance(theme, str) or (
        allowed_themes is not None and theme not in allowed_themes
    ):
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
