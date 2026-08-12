"""Shared resizable-window creation and minimum-size enforcement."""

from __future__ import annotations

import pygame


def open_resizable_window(size: tuple[int, int], caption: str) -> pygame.Surface:
    pygame.display.set_caption(caption)
    return pygame.display.set_mode(size, pygame.RESIZABLE)


def resize_resizable_window(
    requested_size: tuple[int, int],
    minimum_size: tuple[int, int],
) -> pygame.Surface:
    width = max(minimum_size[0], requested_size[0])
    height = max(minimum_size[1], requested_size[1])
    return pygame.display.set_mode((width, height), pygame.RESIZABLE)
