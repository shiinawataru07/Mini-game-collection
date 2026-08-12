"""Small visual effects derived from rule transitions."""

from __future__ import annotations

from dataclasses import dataclass

from .config import LINE_CLEAR_ANIMATION_MS
from .logic import Transition


@dataclass(frozen=True)
class LineClearAnimation:
    rows: tuple[int, ...]
    started_at: int

    def progress(self, now: int) -> float:
        return min(1.0, max(0.0, (now - self.started_at) / LINE_CLEAR_ANIMATION_MS))

    def finished(self, now: int) -> bool:
        return now - self.started_at >= LINE_CLEAR_ANIMATION_MS


def animation_from_transition(
    transition: Transition,
    started_at: int,
) -> LineClearAnimation | None:
    if not transition.cleared_rows:
        return None
    return LineClearAnimation(transition.cleared_rows, started_at)
