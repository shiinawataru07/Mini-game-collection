"""Synthesized sound helpers with graceful mixer fallback."""

from __future__ import annotations

import math
from array import array
from collections.abc import Mapping

import pygame

from .app_settings import AppSettings

SAMPLE_RATE = 44_100


def tone_samples(
    frequency: float,
    duration_ms: int,
    *,
    amplitude: float = 0.22,
    wave: str = "sine",
) -> list[float]:
    count = max(1, round(SAMPLE_RATE * duration_ms / 1000))
    samples: list[float] = []
    for index in range(count):
        progress = index / count
        phase = math.tau * frequency * index / SAMPLE_RATE
        oscillator = math.sin(phase) if wave == "sine" else 1.0 if math.sin(phase) >= 0 else -1.0
        attack = min(1.0, progress * 24)
        envelope = attack * (1.0 - progress) ** 1.7
        samples.append(oscillator * envelope * amplitude)
    return samples


def sequence_samples(
    notes: tuple[tuple[float, int], ...],
    *,
    amplitude: float = 0.22,
) -> list[float]:
    samples: list[float] = []
    for frequency, duration_ms in notes:
        samples.extend(tone_samples(frequency, duration_ms, amplitude=amplitude))
    return samples


def sound_from_samples(samples: list[float]) -> pygame.mixer.Sound:
    mixer_init = pygame.mixer.get_init()
    if mixer_init is None:
        raise pygame.error("Mixer is unavailable")
    _, _, channels = mixer_init
    pcm = array("h")
    for sample in samples:
        encoded = round(max(-1.0, min(1.0, sample)) * 32767)
        pcm.extend([encoded] * channels)
    return pygame.mixer.Sound(buffer=pcm.tobytes())


class SoundBank:
    """Create synthesized effects once and apply live global volume when played."""

    def __init__(self, samples: Mapping[str, list[float]], settings: AppSettings) -> None:
        self.settings = settings
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            self.sounds = {name: sound_from_samples(values) for name, values in samples.items()}
        except (pygame.error, ValueError):
            self.sounds = {}

    def update_settings(self, settings: AppSettings) -> None:
        self.settings = settings

    def play(self, name: str, gain: float = 1.0) -> None:
        sound = self.sounds.get(name)
        if sound is None or self.settings.effective_volume <= 0:
            return
        sound.set_volume(max(0.0, min(1.0, self.settings.effective_volume * gain)))
        sound.play()
