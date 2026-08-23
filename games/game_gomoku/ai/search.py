"""Iterative-deepening negamax search for Gomoku."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum

from ..logic import GameState, Position
from .api import SearchLimits, SearchResult
from .evaluate import evaluate
from .movegen import ordered_moves
from .position import SearchPosition
from .threats import find_vcf

MATE_SCORE = 10_000_000
INFINITY = MATE_SCORE + 1_000_000


class _Bound(IntEnum):
    EXACT = 0
    LOWER = 1
    UPPER = 2


@dataclass(frozen=True)
class _Entry:
    key: int
    depth: int
    score: int
    bound: _Bound
    move: Position | None


class _TranspositionTable:
    def __init__(self, capacity: int) -> None:
        self._slots: list[_Entry | None] = [None] * capacity

    def get(self, key: int) -> _Entry | None:
        entry = self._slots[key % len(self._slots)]
        return entry if entry is not None and entry.key == key else None

    def store(self, entry: _Entry) -> None:
        index = entry.key % len(self._slots)
        previous = self._slots[index]
        if previous is None or previous.key == entry.key or entry.depth >= previous.depth:
            self._slots[index] = entry


class _SearchStopped(Exception):
    pass


class _Engine:
    def __init__(
        self,
        position: SearchPosition,
        limits: SearchLimits,
        cancel: Callable[[], bool] | None,
    ) -> None:
        self.position = position
        self.limits = limits
        self.cancel = cancel
        self.started = time.perf_counter()
        self.deadline = self.started + limits.time_ms / 1000
        self.nodes = 0
        self.table = _TranspositionTable(limits.table_capacity)

    def stopped(self) -> bool:
        return (
            time.perf_counter() >= self.deadline
            or (self.cancel is not None and self.cancel())
            or (self.limits.max_nodes is not None and self.nodes >= self.limits.max_nodes)
        )

    def check_stopped(self) -> None:
        if self.stopped():
            raise _SearchStopped

    def search(self) -> SearchResult:
        if not self.position.moves:
            center = (7, 7)
            return self.result(center, 0, 0, (center,))

        fallback_moves = ordered_moves(self.position, limit=1)
        if not fallback_moves:
            return self.result(None, 0, 0, ())
        best_move = fallback_moves[0]
        best_score = 0
        best_pv: tuple[Position, ...] = (best_move,)
        completed_depth = 0
        maximum = self.limits.max_depth or 64

        if self.limits.vcf_depth:
            vcf_deadline = min(
                self.deadline,
                self.started + self.limits.time_ms * 0.35 / 1000,
            )

            def stop_vcf() -> bool:
                return (
                    time.perf_counter() >= vcf_deadline
                    or (self.cancel is not None and self.cancel())
                    or (self.limits.max_nodes is not None and self.nodes >= self.limits.max_nodes)
                )

            vcf = find_vcf(self.position, self.limits.vcf_depth, stop_vcf)
            if vcf is not None:
                self.nodes += vcf.nodes
                return self.result(
                    vcf.line[0],
                    MATE_SCORE - len(vcf.line),
                    len(vcf.line),
                    vcf.line,
                )

        for depth in range(1, maximum + 1):
            try:
                score, pv = self.negamax(depth, -INFINITY, INFINITY, 0)
            except _SearchStopped:
                break
            if pv:
                best_move = pv[0]
                best_pv = pv
                best_score = score
                completed_depth = depth
            if abs(score) >= MATE_SCORE - 225:
                break

        return self.result(best_move, best_score, completed_depth, best_pv)

    def negamax(
        self,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
    ) -> tuple[int, tuple[Position, ...]]:
        self.check_stopped()
        self.nodes += 1

        if self.position.moves:
            latest = self.position.moves[-1]
            if self.position.is_win_at(latest):
                return -MATE_SCORE + ply, ()
        if depth == 0:
            return evaluate(self.position), ()

        original_alpha = alpha
        entry = self.table.get(self.position.hash_key)
        if entry is not None and entry.depth >= depth:
            if entry.bound == _Bound.EXACT:
                return entry.score, (entry.move,) if entry.move is not None else ()
            if entry.bound == _Bound.LOWER:
                alpha = max(alpha, entry.score)
            else:
                beta = min(beta, entry.score)
            if alpha >= beta:
                return entry.score, (entry.move,) if entry.move is not None else ()

        preferred = entry.move if entry is not None else None
        candidate_limit = 24 if ply == 0 else 14 if depth >= 2 else 18
        moves = ordered_moves(self.position, preferred, candidate_limit)
        if not moves:
            return 0, ()

        best_score = -INFINITY
        best_move: Position | None = None
        best_child_pv: tuple[Position, ...] = ()
        for move_index, move in enumerate(moves):
            self.position.make_move(move)
            try:
                if move_index == 0:
                    child_score, child_pv = self.negamax(depth - 1, -beta, -alpha, ply + 1)
                    score = -child_score
                else:
                    child_score, child_pv = self.negamax(
                        depth - 1,
                        -alpha - 1,
                        -alpha,
                        ply + 1,
                    )
                    score = -child_score
                    if alpha < score < beta:
                        child_score, child_pv = self.negamax(
                            depth - 1,
                            -beta,
                            -alpha,
                            ply + 1,
                        )
                        score = -child_score
            finally:
                self.position.unmake_move()
            if score > best_score:
                best_score = score
                best_move = move
                best_child_pv = child_pv
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        bound = _Bound.EXACT
        if best_score <= original_alpha:
            bound = _Bound.UPPER
        elif best_score >= beta:
            bound = _Bound.LOWER
        self.table.store(_Entry(self.position.hash_key, depth, best_score, bound, best_move))
        pv = (best_move, *best_child_pv) if best_move is not None else ()
        return best_score, pv

    def result(
        self,
        move: Position | None,
        score: int,
        depth: int,
        pv: tuple[Position, ...],
    ) -> SearchResult:
        elapsed_ms = max(0, round((time.perf_counter() - self.started) * 1000))
        return SearchResult(
            move,
            score,
            depth,
            self.nodes,
            elapsed_ms,
            pv,
            score >= MATE_SCORE - 225,
        )


def run_search(
    state: GameState,
    limits: SearchLimits,
    cancel: Callable[[], bool] | None,
) -> SearchResult:
    if state.status != "playing":
        return SearchResult(None, 0, 0, 0, 0, ())
    engine = _Engine(SearchPosition.from_state(state), limits, cancel)
    return engine.search()
