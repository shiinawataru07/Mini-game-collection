"""Menu preview renderer for Snake."""

from __future__ import annotations

import pygame


def draw_preview(screen: pygame.Surface, rect: pygame.Rect) -> None:
    preview = pygame.Rect(0, 0, min(170, rect.width - 50), min(128, rect.height // 2))
    preview.center = (rect.centerx, rect.top + rect.height // 3)
    pygame.draw.rect(screen, (210, 226, 194), preview, border_radius=10)
    cell = max(14, min(preview.width // 9, preview.height // 6))
    cells = ((2, 3), (3, 3), (4, 3), (5, 3), (5, 2), (6, 2))
    origin_x = preview.centerx - cell * 4
    origin_y = preview.centery - cell * 3
    for index, (column, row) in enumerate(cells):
        segment = pygame.Rect(
            origin_x + column * cell + 1,
            origin_y + row * cell + 1,
            cell - 2,
            cell - 2,
        )
        pygame.draw.rect(
            screen,
            (63, 125, 68) if index == len(cells) - 1 else (91, 151, 83),
            segment,
            border_radius=cell // 3,
        )
    food_center = (origin_x + 7 * cell + cell // 2, origin_y + 2 * cell + cell // 2)
    pygame.draw.circle(screen, (218, 73, 65), food_center, max(4, cell // 3))
