"""Core 2048 rules with no dependency on Pygame or persistence."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

Board = list[list[int]]
Direction = Literal["up", "down", "left", "right"]

BOARD_SIZE = 4
NEW_TILE_FOUR_CHANCE = 0.1


@dataclass
class GameState:
    """Everything needed to describe one 2048 game."""

    board: Board
    score: int = 0
    game_over: bool = False


def create_empty_board(size: int = BOARD_SIZE) -> Board:
    return [[0 for _ in range(size)] for _ in range(size)]


def merge_line(line: list[int]) -> tuple[list[int], int]:
    """Slide and merge one row to the left, returning its earned score."""

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
