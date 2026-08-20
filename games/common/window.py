"""Shared resizable-window creation and minimum-size enforcement."""

from __future__ import annotations

import pygame

_windowed_size = (760, 600)


def open_resizable_window(
    size: tuple[int, int],
    caption: str,
    fullscreen: bool = False,
) -> pygame.Surface:
    global _windowed_size

    pygame.display.set_caption(caption)
    _windowed_size = size
    if fullscreen:
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    return pygame.display.set_mode(size, pygame.RESIZABLE)


def resize_resizable_window(
    requested_size: tuple[int, int],
    minimum_size: tuple[int, int],
) -> pygame.Surface:
    global _windowed_size

    surface = pygame.display.get_surface()
    if surface is not None and surface.get_flags() & pygame.FULLSCREEN:
        return surface
    width = max(minimum_size[0], requested_size[0])
    height = max(minimum_size[1], requested_size[1])
    _windowed_size = (width, height)
    return pygame.display.set_mode((width, height), pygame.RESIZABLE)


def set_fullscreen(
    enabled: bool,
    minimum_size: tuple[int, int],
) -> pygame.Surface:
    """Switch display mode while preserving the last windowed size."""

    global _windowed_size

    surface = pygame.display.get_surface()
    if enabled:
        if surface is not None and not surface.get_flags() & pygame.FULLSCREEN:
            _windowed_size = surface.get_size()
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    width = max(minimum_size[0], _windowed_size[0])
    height = max(minimum_size[1], _windowed_size[1])
    _windowed_size = (width, height)
    return pygame.display.set_mode(_windowed_size, pygame.RESIZABLE)
