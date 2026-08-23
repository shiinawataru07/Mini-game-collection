"""Static evaluation from the perspective of the side to move."""

from __future__ import annotations

from .movegen import nearby_candidates
from .patterns import move_potential
from .position import SearchPosition


def evaluate(position: SearchPosition) -> int:
    candidates = nearby_candidates(position)
    if not candidates:
        return 0
    player = position.current_player
    opponent = 3 - player
    attacks = sorted((move_potential(position, move, player) for move in candidates), reverse=True)[
        :6
    ]
    defenses = sorted(
        (move_potential(position, move, opponent) for move in candidates), reverse=True
    )[:6]
    weights = (100, 45, 24, 14, 8, 4)
    attack_score = sum(score * weight for score, weight in zip(attacks, weights, strict=False))
    defense_score = sum(score * weight for score, weight in zip(defenses, weights, strict=False))
    return (attack_score - defense_score * 11 // 10) // 100
