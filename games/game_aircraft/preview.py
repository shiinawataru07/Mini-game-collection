"""Menu preview for Pixel Aircraft Battle."""

from __future__ import annotations

import pygame


def _sprite(
    screen: pygame.Surface,
    pattern: tuple[str, ...],
    center: tuple[int, int],
    pixel: int,
    colors: dict[str, tuple[int, int, int]],
) -> None:
    left = center[0] - len(pattern[0]) * pixel // 2
    top = center[1] - len(pattern) * pixel // 2
    for row, line in enumerate(pattern):
        for column, symbol in enumerate(line):
            if symbol in colors:
                pygame.draw.rect(
                    screen,
                    colors[symbol],
                    (left + column * pixel, top + row * pixel, pixel, pixel),
                )


def draw_preview(screen: pygame.Surface, rect: pygame.Rect) -> None:
    preview = pygame.Rect(0, 0, min(170, rect.width - 44), min(128, rect.height // 2))
    preview.center = (rect.centerx, rect.top + rect.height // 3)
    pygame.draw.rect(screen, (10, 17, 37), preview, border_radius=4)
    for index in range(16):
        x = preview.left + 7 + (index * 41) % max(8, preview.width - 14)
        y = preview.top + 6 + (index * 29) % max(8, preview.height - 12)
        pygame.draw.rect(screen, (61, 91, 130), (x, y, 2, 2))
    player = ("...C...", "..CCC..", ".CCWCC.", "CCCCCCC", "..Y.Y..")
    enemy = ("R.....R", ".RR.RR.", "RRRWRRR", ".R.R.R.")
    _sprite(
        screen,
        enemy,
        (preview.centerx + 29, preview.top + 32),
        3,
        {"R": (255, 88, 104), "W": (240, 246, 255)},
    )
    _sprite(
        screen,
        player,
        (preview.centerx - 22, preview.bottom - 27),
        3,
        {"C": (55, 226, 213), "W": (240, 246, 255), "Y": (255, 218, 91)},
    )
    pygame.draw.rect(screen, (55, 226, 213), (preview.centerx - 23, preview.centery - 9, 3, 17))
    pygame.draw.rect(screen, (255, 218, 91), (preview.centerx + 5, preview.centery - 24, 3, 3))
