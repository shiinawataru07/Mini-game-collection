"""Synthesized arcade sound effects for Pixel Aircraft Battle."""

from __future__ import annotations

from games.common.app_settings import AppSettings
from games.common.audio import SoundBank, sequence_samples, tone_samples

from .logic import Transition


class GameSounds:
    def __init__(self, settings: AppSettings) -> None:
        self.bank = SoundBank(
            {
                "shot": tone_samples(660, 24, amplitude=0.055, wave="square"),
                "hit": tone_samples(150, 32, amplitude=0.1, wave="square"),
                "destroyed": sequence_samples(((220, 28), (120, 75)), amplitude=0.15),
                "elite_destroyed": sequence_samples(
                    ((330, 35), (220, 45), (130, 100)), amplitude=0.18
                ),
                "boss_warning": sequence_samples(
                    ((110, 120), (146.8, 120), (110, 180)), amplitude=0.2
                ),
                "boss_defeated": sequence_samples(
                    ((196, 65), (261.6, 65), (329.6, 65), (523.3, 180)), amplitude=0.22
                ),
                "hurt": sequence_samples(((180, 90), (110, 130)), amplitude=0.2),
                "shield": sequence_samples(((440, 45), (700, 90)), amplitude=0.15),
                "powerup": sequence_samples(((523, 45), (659, 45), (880, 90)), amplitude=0.16),
                "game_over": sequence_samples(((330, 90), (220, 110), (110, 190)), amplitude=0.2),
            },
            settings,
        )

    def update_settings(self, settings: AppSettings) -> None:
        self.bank.update_settings(settings)

    def play_transition(self, transition: Transition) -> None:
        events = transition.events
        if "game_over" in events:
            self.bank.play("game_over")
        elif "boss_defeated" in events:
            self.bank.play("boss_defeated")
        elif "hurt" in events:
            self.bank.play("hurt")
        elif "shield" in events:
            self.bank.play("shield")
        elif "boss_warning" in events:
            self.bank.play("boss_warning")
        elif "powerup" in events:
            self.bank.play("powerup")
        elif "elite_destroyed" in events:
            self.bank.play("elite_destroyed")
        elif "destroyed" in events:
            self.bank.play("destroyed")
        elif "hit" in events:
            self.bank.play("hit")
        elif "shot" in events:
            self.bank.play("shot", gain=0.45)
