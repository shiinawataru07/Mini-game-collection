"""Synthesized feedback for 2048 moves and outcomes."""

from __future__ import annotations

from games.common.app_settings import AppSettings
from games.common.audio import SoundBank, sequence_samples, tone_samples

from .animation import MoveAnimation


class GameSounds:
    def __init__(self, settings: AppSettings) -> None:
        self.bank = SoundBank(
            {
                "move": tone_samples(220, 42, amplitude=0.12),
                "merge": sequence_samples(((392, 55), (523.25, 75)), amplitude=0.18),
                "game_over": sequence_samples(((261.63, 110), (196, 150)), amplitude=0.2),
            },
            settings,
        )

    def update_settings(self, settings: AppSettings) -> None:
        self.bank.update_settings(settings)

    def play_move(self, animation: MoveAnimation) -> None:
        self.bank.play("merge" if animation.gained_score else "move")

    def play_game_over(self) -> None:
        self.bank.play("game_over")
