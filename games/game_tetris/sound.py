"""Synthesized feedback for Tetris actions and transitions."""

from __future__ import annotations

from games.common.app_settings import AppSettings
from games.common.audio import SoundBank, sequence_samples, tone_samples

from .logic import Transition


class GameSounds:
    def __init__(self, settings: AppSettings) -> None:
        self.bank = SoundBank(
            {
                "rotate": tone_samples(440, 38, amplitude=0.1),
                "hold": sequence_samples(((330, 45), (415.3, 55)), amplitude=0.12),
                "lock": tone_samples(125, 55, amplitude=0.16, wave="square"),
                "clear_1": sequence_samples(((523.25, 55), (659.25, 75)), amplitude=0.17),
                "clear_2": sequence_samples(
                    ((523.25, 50), (659.25, 50), (783.99, 80)), amplitude=0.18
                ),
                "clear_3": sequence_samples(
                    ((523.25, 45), (659.25, 45), (783.99, 45), (987.77, 90)),
                    amplitude=0.19,
                ),
                "clear_4": sequence_samples(
                    ((392, 45), (523.25, 45), (659.25, 45), (783.99, 45), (1046.5, 120)),
                    amplitude=0.21,
                ),
                "game_over": sequence_samples(
                    ((246.94, 90), (185, 110), (123.47, 180)), amplitude=0.2
                ),
            },
            settings,
        )

    def update_settings(self, settings: AppSettings) -> None:
        self.bank.update_settings(settings)

    def play_transition(self, transition: Transition) -> None:
        if "game_over" in transition.events:
            self.bank.play("game_over")
        elif transition.cleared_rows:
            self.bank.play(f"clear_{min(4, len(transition.cleared_rows))}")
        elif "locked" in transition.events:
            self.bank.play("lock")
        elif "held" in transition.events:
            self.bank.play("hold")
        elif "rotated" in transition.events:
            self.bank.play("rotate")
