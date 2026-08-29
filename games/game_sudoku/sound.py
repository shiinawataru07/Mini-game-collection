"""Synthesized sound feedback for Sudoku actions."""

from __future__ import annotations

from games.common.app_settings import AppSettings
from games.common.audio import SoundBank, sequence_samples, tone_samples

from .logic import Transition


class GameSounds:
    def __init__(self, settings: AppSettings) -> None:
        self.bank = SoundBank(
            {
                "place": tone_samples(440, 42, amplitude=0.1),
                "note": tone_samples(330, 30, amplitude=0.07),
                "error": sequence_samples(((180, 65), (145, 85)), amplitude=0.14),
                "hint": sequence_samples(((523.25, 55), (659.25, 80)), amplitude=0.14),
                "history": tone_samples(260, 35, amplitude=0.07),
                "win": sequence_samples(
                    ((523.25, 75), (659.25, 75), (783.99, 90), (1046.5, 190)),
                    amplitude=0.2,
                ),
            },
            settings,
        )

    def update_settings(self, settings: AppSettings) -> None:
        self.bank.update_settings(settings)

    def play_transition(self, transition: Transition) -> None:
        if "won" in transition.events:
            self.bank.play("win")
        elif "error" in transition.events:
            self.bank.play("error")
        elif "hint" in transition.events:
            self.bank.play("hint")
        elif "note" in transition.events:
            self.bank.play("note")
        elif any(event in transition.events for event in ("undo", "redo", "cleared")):
            self.bank.play("history")
        elif "placed" in transition.events:
            self.bank.play("place")
