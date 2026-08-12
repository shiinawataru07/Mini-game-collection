"""Expectimax-based 2048 AI with no dependency on Pygame."""

from __future__ import annotations

import math
from functools import cache

from .logic import Board, Direction, empty_cells, move_board

BoardTuple = tuple[tuple[int, ...], ...]
SpawnOutcome = tuple[Board, float]

DIRECTION_ORDER: tuple[Direction, ...] = ("up", "left", "right", "down")
DEFAULT_SEARCH_DEPTH = 3


def _freeze(board: Board) -> BoardTuple:
    return tuple(tuple(row) for row in board)


def _thaw(board: BoardTuple) -> Board:
    return [list(row) for row in board]


def legal_moves(board: Board) -> list[tuple[Direction, Board, int]]:
    """Return all valid directions with their resulting boards and scores."""

    moves: list[tuple[Direction, Board, int]] = []
    for direction in DIRECTION_ORDER:
        moved, score, changed = move_board(board, direction)
        if changed:
            moves.append((direction, moved, score))
    return moves


def spawn_outcomes(board: Board) -> list[SpawnOutcome]:
    """Return every possible random tile outcome and its exact probability."""

    available = empty_cells(board)
    if not available:
        return [(row_copy(board), 1.0)]

    outcomes: list[SpawnOutcome] = []
    cell_probability = 1.0 / len(available)
    for row, column in available:
        for value, value_probability in ((2, 0.9), (4, 0.1)):
            spawned = row_copy(board)
            spawned[row][column] = value
            outcomes.append((spawned, cell_probability * value_probability))
    return outcomes


def row_copy(board: Board) -> Board:
    return [row[:] for row in board]


def _log_value(value: int) -> float:
    return math.log2(value) if value else 0.0


def _smoothness(board: Board) -> float:
    """Reward neighboring tiles with similar values."""

    penalty = 0.0
    size = len(board)
    for row in range(size):
        for column in range(size):
            if not board[row][column]:
                continue
            current = _log_value(board[row][column])
            if column + 1 < size and board[row][column + 1]:
                penalty += abs(current - _log_value(board[row][column + 1]))
            if row + 1 < size and board[row + 1][column]:
                penalty += abs(current - _log_value(board[row + 1][column]))
    return -penalty


def _monotonicity(board: Board) -> float:
    """Reward rows and columns whose values consistently follow one direction."""

    totals = [0.0, 0.0, 0.0, 0.0]
    size = len(board)
    for row in range(size):
        for column in range(size - 1):
            current = _log_value(board[row][column])
            following = _log_value(board[row][column + 1])
            if current > following:
                totals[0] += following - current
            else:
                totals[1] += current - following
    for column in range(size):
        for row in range(size - 1):
            current = _log_value(board[row][column])
            following = _log_value(board[row + 1][column])
            if current > following:
                totals[2] += following - current
            else:
                totals[3] += current - following
    return max(totals[0], totals[1]) + max(totals[2], totals[3])


def _merge_potential(board: Board) -> int:
    pairs = 0
    size = len(board)
    for row in range(size):
        for column in range(size):
            value = board[row][column]
            if not value:
                continue
            if column + 1 < size and value == board[row][column + 1]:
                pairs += 1
            if row + 1 < size and value == board[row + 1][column]:
                pairs += 1
    return pairs


def evaluate_board(board: Board) -> float:
    """Estimate how promising a board is; higher values are better."""

    available = len(empty_cells(board))
    maximum = max(max(row) for row in board)
    max_log = _log_value(maximum)
    corners = (board[0][0], board[0][-1], board[-1][0], board[-1][-1])
    corner_bonus = max_log * 120 if maximum in corners else 0.0

    return (
        available * 280
        + _monotonicity(board) * 45
        + _smoothness(board) * 14
        + _merge_potential(board) * 90
        + corner_bonus
        + max_log * 20
    )


def choose_move(board: Board, depth: int = DEFAULT_SEARCH_DEPTH) -> Direction | None:
    """Choose a legal direction with expectimax without mutating the board."""

    if depth < 1:
        raise ValueError("Search depth must be at least 1.")

    @cache
    def max_value(frozen: BoardTuple, remaining: int) -> float:
        current = _thaw(frozen)
        moves = legal_moves(current)
        if remaining <= 0 or not moves:
            return evaluate_board(current)
        return max(
            gained_score * 0.2 + chance_value(_freeze(moved), remaining - 1)
            for _, moved, gained_score in moves
        )

    @cache
    def chance_value(frozen: BoardTuple, remaining: int) -> float:
        current = _thaw(frozen)
        if remaining <= 0:
            return evaluate_board(current)
        return sum(
            probability * max_value(_freeze(outcome), remaining - 1)
            for outcome, probability in spawn_outcomes(current)
        )

    best_direction: Direction | None = None
    best_value = float("-inf")
    for direction, moved, gained_score in legal_moves(board):
        value = gained_score * 0.2 + chance_value(_freeze(moved), depth - 1)
        if value > best_value:
            best_value = value
            best_direction = direction
    return best_direction
