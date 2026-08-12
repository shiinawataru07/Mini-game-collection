"""Frame-rate-independent held-key repeat for horizontal Tetris movement."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .config import ARR_MS, DAS_MS

HorizontalDirection = Literal["left", "right"]


@dataclass
class HorizontalInput:
    das_ms: float = DAS_MS
    arr_ms: float = ARR_MS
    held: list[HorizontalDirection] = field(default_factory=list)
    elapsed_ms: float = 0.0
    repeating: bool = False

    @property
    def active(self) -> HorizontalDirection | None:
        return self.held[-1] if self.held else None

    def press(self, direction: HorizontalDirection) -> HorizontalDirection | None:
        if direction in self.held:
            return None
        self.held.append(direction)
        self.elapsed_ms = 0.0
        self.repeating = False
        return direction

    def release(self, direction: HorizontalDirection) -> HorizontalDirection | None:
        was_active = self.active == direction
        if direction in self.held:
            self.held.remove(direction)
        self.elapsed_ms = 0.0
        self.repeating = False
        return self.active if was_active else None

    def advance(self, elapsed_ms: float) -> tuple[HorizontalDirection, ...]:
        if elapsed_ms < 0:
            raise ValueError("Elapsed time must not be negative.")
        direction = self.active
        if direction is None:
            return ()
        self.elapsed_ms += elapsed_ms
        threshold = self.arr_ms if self.repeating else self.das_ms
        actions: list[HorizontalDirection] = []
        while self.elapsed_ms >= threshold:
            self.elapsed_ms -= threshold
            actions.append(direction)
            self.repeating = True
            threshold = self.arr_ms
        return tuple(actions)

    def reset(self) -> None:
        self.held.clear()
        self.elapsed_ms = 0.0
        self.repeating = False
