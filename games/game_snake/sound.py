"""Synthesized feedback for Snake food and terminal outcomes."""

from __future__ import annotations

from games.common.app_settings import AppSettings
from games.common.audio import SoundBank, sequence_samples, tone_samples

from .logic import StepResult


class GameSounds:
    def __init__(self, settings: AppSettings) -> None:
        self.bank = SoundBank(
            {
                "food": tone_samples(620, 65, amplitude=0.16),
                "bonus": sequence_samples(((659.25, 60), (987.77, 95)), amplitude=0.2),
                "collision": sequence_samples(((150, 90), (95, 160)), amplitude=0.2),
                "win": sequence_samples(
                    ((523.25, 75), (659.25, 75), (783.99, 75), (1046.5, 140)),
                    amplitude=0.2,
                ),
            },
            settings,
        )

    def update_settings(self, settings: AppSettings) -> None:
        self.bank.update_settings(settings)

    def play_step(self, result: StepResult) -> None:
        if result.state.status == "won":
            self.bank.play("win")
        elif result.collision is not None:
            self.bank.play("collision")
        elif result.ate_bonus:
            self.bank.play("bonus")
        elif result.ate_food:
            self.bank.play("food")
