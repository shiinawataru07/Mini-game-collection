"""Menu preview renderer for Tetris."""

from __future__ import annotations

import pygame


def draw_preview(screen: pygame.Surface, rect: pygame.Rect) -> None:
    cell = max(8, min(18, rect.width // 13, rect.height // 11))
    columns, rows = 8, 6
    board = pygame.Rect(0, 0, columns * cell, rows * cell)
    board.center = (rect.centerx, rect.top + rect.height // 3)
    pygame.draw.rect(screen, (21, 26, 43), board.inflate(10, 10), border_radius=8)
    blocks = {
        (0, 5): (69, 116, 232),
        (1, 5): (69, 116, 232),
        (2, 5): (69, 116, 232),
        (2, 4): (69, 116, 232),
        (3, 5): (83, 209, 104),
        (4, 5): (83, 209, 104),
        (4, 4): (83, 209, 104),
        (5, 4): (83, 209, 104),
        (6, 5): (246, 211, 66),
        (7, 5): (246, 211, 66),
        (6, 4): (246, 211, 66),
        (7, 4): (246, 211, 66),
        (3, 3): (172, 91, 235),
        (4, 3): (172, 91, 235),
        (5, 3): (172, 91, 235),
        (4, 2): (172, 91, 235),
    }
    for row in range(rows):
        for column in range(columns):
            cell_rect = pygame.Rect(
                board.left + column * cell + 1,
                board.top + row * cell + 1,
                cell - 2,
                cell - 2,
            )
            color = blocks.get((column, row), (39, 46, 68))
            pygame.draw.rect(screen, color, cell_rect, border_radius=2)
