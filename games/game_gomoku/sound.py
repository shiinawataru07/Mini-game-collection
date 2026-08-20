"""Restrained synthesized stone and outcome sounds for Gomoku."""

from games.common.app_settings import AppSettings
from games.common.audio import SoundBank, sequence_samples, tone_samples

from .logic import MoveResult


class GameSounds:
    def __init__(self, settings: AppSettings) -> None:
        self.bank = SoundBank(
            {
                "stone": tone_samples(165, 52, amplitude=0.16, wave="square"),
                "undo": tone_samples(245, 55, amplitude=0.1),
                "win": sequence_samples(
                    ((392, 75), (523.25, 75), (659.25, 75), (783.99, 140)),
                    amplitude=0.18,
                ),
            },
            settings,
        )

    def update_settings(self, settings: AppSettings) -> None:
        self.bank.update_settings(settings)

    def play_move(self, result: MoveResult) -> None:
        if result.won:
            self.bank.play("win")
        elif result.placed:
            self.bank.play("stone")

    def play_undo(self) -> None:
        self.bank.play("undo")
