"""Threat-safe candidate generation and deterministic move ordering."""

from __future__ import annotations

from ..config import BOARD_SIZE
from ..logic import Position
from .patterns import move_potential
from .position import SearchPosition

CENTER = BOARD_SIZE // 2


def nearby_candidates(position: SearchPosition, radius: int = 2) -> list[Position]:
    if not position.moves:
        return [(CENTER, CENTER)]

    candidates: set[Position] = set()
    for move_row, move_column in position.moves:
        for row in range(max(0, move_row - radius), min(BOARD_SIZE, move_row + radius + 1)):
            for column in range(
                max(0, move_column - radius), min(BOARD_SIZE, move_column + radius + 1)
            ):
                if position.board[row][column] == 0:
                    candidates.add((row, column))
    return sorted(candidates)


def winning_moves(
    position: SearchPosition,
    player: int,
    candidates: list[Position] | None = None,
) -> list[Position]:
    available = nearby_candidates(position) if candidates is None else candidates
    return [move for move in available if position.is_winning_move(move, player)]


def ordered_moves(
    position: SearchPosition,
    preferred: Position | None = None,
    limit: int | None = None,
) -> list[Position]:
    candidates = nearby_candidates(position)
    player = position.current_player
    opponent = 3 - player

    wins = winning_moves(position, player, candidates)
    if wins:
        return _prefer(wins, preferred)

    forced_blocks = winning_moves(position, opponent, candidates)
    if forced_blocks:
        return _prefer(forced_blocks, preferred)

    scored = []
    for row, column in candidates:
        move = (row, column)
        attack = move_potential(position, move, player)
        defense = move_potential(position, move, opponent)
        center_distance = abs(row - CENTER) + abs(column - CENTER)
        score = attack * 2 + defense - center_distance
        if move == preferred:
            score += 2_000_000
        scored.append((score, move))
    scored.sort(key=lambda item: (-item[0], item[1]))
    moves = [move for _, move in scored]
    return moves if limit is None else moves[:limit]


def _prefer(moves: list[Position], preferred: Position | None) -> list[Position]:
    return sorted(moves, key=lambda move: (move != preferred, move))
