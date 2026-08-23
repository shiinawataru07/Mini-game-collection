"""Deterministic Zobrist keys for Gomoku positions."""

from __future__ import annotations

import random

from ..config import BOARD_SIZE

_random = random.Random(0x474F4D4F4B55)

STONE_KEYS: tuple[tuple[tuple[int, int], ...], ...] = tuple(
    tuple((_random.getrandbits(64), _random.getrandbits(64)) for _ in range(BOARD_SIZE))
    for _ in range(BOARD_SIZE)
)
SIDE_KEY = _random.getrandbits(64)


def hash_board(board: list[list[int]], current_player: int) -> int:
    """Return the stable hash for a board and side to move."""

    value = SIDE_KEY if current_player == 2 else 0
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            player = board[row][column]
            if player:
                value ^= STONE_KEYS[row][column][player - 1]
    return value
