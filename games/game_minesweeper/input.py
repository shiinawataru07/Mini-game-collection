"""Mouse gesture state for traditional Minesweeper controls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .logic import Position

MouseAction = Literal["reveal", "mark", "chord"]


@dataclass
class BoardMouseInput:
    """Delay single clicks until release so both buttons can form a chord."""

    pressed: dict[int, Position] = field(default_factory=dict)
    chord_consumed: bool = False

    def press(
        self,
        button: int,
        position: Position,
        chord_available: bool,
    ) -> MouseAction | None:
        if button not in (1, 3):
            return None
        self.pressed[button] = position
        if self.pressed.get(1) == self.pressed.get(3) == position:
            self.chord_consumed = True
            return "chord" if chord_available else None
        return None

    def release(self, button: int, position: Position | None) -> MouseAction | None:
        pressed_position = self.pressed.pop(button, None)
        if pressed_position is None:
            return None
        if self.chord_consumed:
            if not self.pressed:
                self.chord_consumed = False
            return None
        if position != pressed_position:
            return None
        return "reveal" if button == 1 else "mark"

    def reset(self) -> None:
        self.pressed.clear()
        self.chord_consumed = False
