"""Small synthesized sound effects for Minesweeper outcomes."""

from __future__ import annotations

import math
import random
from array import array

import pygame

SAMPLE_RATE = 44_100


def _sound_from_samples(samples: list[float]) -> pygame.mixer.Sound:
    mixer_init = pygame.mixer.get_init()
    if mixer_init is None:
        raise pygame.error("Mixer is unavailable")
    _, _, channels = mixer_init
    pcm = array("h")
    for sample in samples:
        value = max(-1.0, min(1.0, sample))
        encoded = round(value * 32767)
        pcm.extend([encoded] * channels)
    return pygame.mixer.Sound(buffer=pcm.tobytes())


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

    def __init__(self) -> None:
        self.victory: pygame.mixer.Sound | None = None
        self.explosion: pygame.mixer.Sound | None = None
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            self.victory = _sound_from_samples(_victory_samples())
            self.explosion = _sound_from_samples(_explosion_samples())
        except (pygame.error, ValueError):
            pass

    def play_victory(self) -> None:
        if self.victory is not None:
            self.victory.play()

    def play_explosion(self) -> None:
        if self.explosion is not None:
            self.explosion.play()


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
