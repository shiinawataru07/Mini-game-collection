"""Deterministic victory-by-continuous-fours (VCF) search."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..logic import Position
from .movegen import nearby_candidates, winning_moves
from .position import SearchPosition


@dataclass(frozen=True)
class VCFResult:
    line: tuple[Position, ...]
    nodes: int


class _VCFStopped(Exception):
    pass


class _VCFSolver:
    def __init__(
        self,
        position: SearchPosition,
        max_attacks: int,
        should_stop: Callable[[], bool] | None,
    ) -> None:
        self.position = position
        self.attacker = position.current_player
        self.defender = 3 - self.attacker
        self.max_attacks = max_attacks
        self.should_stop = should_stop
        self.nodes = 0
        self.failed: set[tuple[int, int]] = set()

    def solve(self) -> VCFResult | None:
        try:
            line = self._attack(self.max_attacks)
        except _VCFStopped:
            return None
        return VCFResult(line, self.nodes) if line else None

    def _check_stopped(self) -> None:
        self.nodes += 1
        if self.should_stop is not None and self.should_stop():
            raise _VCFStopped

    def _attack(self, remaining: int) -> tuple[Position, ...] | None:
        self._check_stopped()
        if self.position.current_player != self.attacker:
            raise RuntimeError("VCF search lost attacker turn")

        wins = winning_moves(self.position, self.attacker)
        if wins:
            return (wins[0],)
        if remaining <= 0 or winning_moves(self.position, self.defender):
            return None

        key = (self.position.hash_key, remaining)
        if key in self.failed:
            return None

        forcing: list[tuple[int, Position, tuple[Position, ...]]] = []
        for move in nearby_candidates(self.position):
            self._check_stopped()
            self.position.make_move(move)
            try:
                if self.position.is_win_at(move, self.attacker):
                    return (move,)
                if winning_moves(self.position, self.defender):
                    continue
                blocks = tuple(winning_moves(self.position, self.attacker))
                if blocks:
                    forcing.append((len(blocks), move, blocks))
            finally:
                self.position.unmake_move()

        forcing.sort(key=lambda item: (-item[0], item[1]))
        for _, move, expected_blocks in forcing:
            self._check_stopped()
            self.position.make_move(move)
            try:
                blocks = tuple(winning_moves(self.position, self.attacker))
                if blocks != expected_blocks:
                    continue
                if len(blocks) >= 2:
                    defense = blocks[0]
                    self.position.make_move(defense)
                    try:
                        finishes = winning_moves(self.position, self.attacker)
                    finally:
                        self.position.unmake_move()
                    if finishes:
                        return move, defense, finishes[0]
                    continue

                defense = blocks[0]
                self.position.make_move(defense)
                try:
                    continuation = self._attack(remaining - 1)
                finally:
                    self.position.unmake_move()
                if continuation:
                    return move, defense, *continuation
            finally:
                self.position.unmake_move()

        self.failed.add(key)
        return None


def find_vcf(
    position: SearchPosition,
    max_attacks: int = 8,
    should_stop: Callable[[], bool] | None = None,
) -> VCFResult | None:
    """Find a forced win where every non-final attack creates an immediate four."""

    if max_attacks < 1:
        raise ValueError("VCF depth must be at least one attacking move")
    return _VCFSolver(position, max_attacks, should_stop).solve()
