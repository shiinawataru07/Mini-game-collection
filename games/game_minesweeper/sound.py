"""Small synthesized sound effects for Minesweeper outcomes."""

from __future__ import annotations

import math
import random

import pygame

from games.common.app_settings import AppSettings, load_app_settings
from games.common.audio import SAMPLE_RATE, sound_from_samples


def _victory_samples() -> list[float]:
    samples: list[float] = []
    for frequency in (523.25, 659.25, 783.99, 1046.5):
        count = round(SAMPLE_RATE * 0.12)
        for index in range(count):
            progress = index / count
            envelope = min(1.0, progress * 18) * (1.0 - progress) ** 1.5
            samples.append(math.sin(math.tau * frequency * index / SAMPLE_RATE) * envelope * 0.24)
    return samples


def _explosion_samples() -> list[float]:
    source = random.Random(2048)
    count = round(SAMPLE_RATE * 0.38)
    samples: list[float] = []
    for index in range(count):
        progress = index / count
        envelope = (1.0 - progress) ** 2.2
        frequency = 115 - progress * 70
        low_tone = math.sin(math.tau * frequency * index / SAMPLE_RATE)
        noise = source.uniform(-1.0, 1.0)
        samples.append((low_tone * 0.38 + noise * 0.42) * envelope)
    return samples


class GameSounds:
    """Load outcome sounds once and degrade silently when audio is unavailable."""

    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or load_app_settings()
        self.victory: pygame.mixer.Sound | None = None
        self.explosion: pygame.mixer.Sound | None = None
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            self.victory = sound_from_samples(_victory_samples())
            self.explosion = sound_from_samples(_explosion_samples())
        except (pygame.error, ValueError):
            pass

    def update_settings(self, settings: AppSettings) -> None:
        self.settings = settings

    def _play(self, sound: pygame.mixer.Sound | None) -> None:
        if sound is None or self.settings.effective_volume <= 0:
            return
        sound.set_volume(self.settings.effective_volume)
        sound.play()

    def play_victory(self) -> None:
        self._play(self.victory)

    def play_explosion(self) -> None:
        self._play(self.explosion)


def play_outcome_transition(
    previous_status: str,
    current_status: str,
    sounds: GameSounds,
) -> None:
    """Play exactly one effect when an action reaches a terminal outcome."""

    if previous_status != "lost" and current_status == "lost":
        sounds.play_explosion()
    elif previous_status != "won" and current_status == "won":
        sounds.play_victory()
