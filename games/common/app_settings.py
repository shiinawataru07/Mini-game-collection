"""Persistent settings that apply to the collection and every game."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

import pygame

from .json_store import load_json_object, save_json_object

APP_SETTINGS_PATH = Path(__file__).with_name(".app_settings.json")
DEFAULT_VOLUME = 70
VOLUME_STEP = 10
GlobalAction = Literal["volume_down", "volume_up", "mute", "fullscreen"]


@dataclass(frozen=True)
class AppSettings:
    volume: int = DEFAULT_VOLUME
    muted: bool = False
    fullscreen: bool = False

    @property
    def effective_volume(self) -> float:
        return 0.0 if self.muted else self.volume / 100


def _valid_volume(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return max(0, min(100, value))
    return DEFAULT_VOLUME


def load_app_settings(path: Path = APP_SETTINGS_PATH) -> AppSettings:
    payload = load_json_object(path)
    if payload is None:
        return AppSettings()
    muted = payload.get("muted")
    fullscreen = payload.get("fullscreen")
    return AppSettings(
        volume=_valid_volume(payload.get("volume")),
        muted=muted if isinstance(muted, bool) else False,
        fullscreen=fullscreen if isinstance(fullscreen, bool) else False,
    )


def save_app_settings(
    settings: AppSettings,
    path: Path = APP_SETTINGS_PATH,
) -> bool:
    return save_json_object(
        path,
        {
            "volume": _valid_volume(settings.volume),
            "muted": settings.muted,
            "fullscreen": settings.fullscreen,
        },
    )


def apply_global_action(settings: AppSettings, action: GlobalAction) -> AppSettings:
    if action == "volume_down":
        return replace(settings, volume=max(0, settings.volume - VOLUME_STEP), muted=False)
    if action == "volume_up":
        return replace(settings, volume=min(100, settings.volume + VOLUME_STEP), muted=False)
    if action == "mute":
        return replace(settings, muted=not settings.muted)
    return replace(settings, fullscreen=not settings.fullscreen)


def global_action_from_key(key: int) -> GlobalAction | None:
    if key == pygame.K_m:
        return "mute"
    if key in (pygame.K_MINUS, pygame.K_KP_MINUS):
        return "volume_down"
    if key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
        return "volume_up"
    if key == pygame.K_F11:
        return "fullscreen"
    return None


def audio_status(settings: AppSettings) -> str:
    return "静音" if settings.muted else f"音量 {settings.volume}%"


def handle_global_shortcut(
    key: int,
    settings: AppSettings,
    minimum_size: tuple[int, int],
) -> tuple[AppSettings, pygame.Surface] | None:
    """Apply and persist a collection-wide keyboard shortcut."""

    action = global_action_from_key(key)
    if action is None:
        return None
    updated = apply_global_action(settings, action)
    save_app_settings(updated)
    if action == "fullscreen":
        from .window import set_fullscreen

        screen = set_fullscreen(updated.fullscreen, minimum_size)
    else:
        screen = pygame.display.get_surface()
        if screen is None:
            raise pygame.error("Display surface is unavailable")
    return updated, screen
