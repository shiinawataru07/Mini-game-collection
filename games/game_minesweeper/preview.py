"""Menu preview renderer for Minesweeper."""

from __future__ import annotations

import pygame

from games.common.fonts import get_font


def draw_preview(screen: pygame.Surface, rect: pygame.Rect) -> None:
    size = min(132, rect.width - 52, rect.height // 2)
    board = pygame.Rect(0, 0, size, size)
    board.center = (rect.centerx, rect.top + rect.height // 3)
    pygame.draw.rect(screen, (116, 129, 145), board, border_radius=8)
    gap = 2
    cell_size = (size - gap * 2) // 5
    values = (
        (None, None, None, 1, 0),
        (None, "flag", None, 1, 0),
        (None, None, None, 2, 1),
        (1, 1, 1, 2, None),
        (0, 0, 0, 1, None),
    )
    colors = {1: (42, 101, 190), 2: (51, 128, 72)}
    for row in range(5):
        for column in range(5):
            cell = pygame.Rect(
                board.left + gap + column * cell_size,
                board.top + gap + row * cell_size,
                cell_size - 1,
                cell_size - 1,
            )
            value = values[row][column]
            hidden = value is None or value == "flag"
            pygame.draw.rect(screen, (177, 188, 201) if hidden else (229, 233, 238), cell)
            if value == "flag":
                pole_x = cell.centerx + 2
                pygame.draw.line(
                    screen, (42, 47, 54), (pole_x, cell.top + 5), (pole_x, cell.bottom - 4), 2
                )
                pygame.draw.polygon(
                    screen,
                    (218, 67, 62),
                    (
                        (pole_x, cell.top + 5),
                        (cell.left + 5, cell.top + 9),
                        (pole_x, cell.top + 12),
                    ),
                )
            elif isinstance(value, int) and value:
                label = get_font(max(12, cell_size // 2), bold=True).render(
                    str(value), True, colors[value]
                )
                screen.blit(label, label.get_rect(center=cell.center))
