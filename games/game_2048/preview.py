"""Menu preview renderer for 2048."""

from __future__ import annotations

import pygame

from games.common.fonts import get_font


def draw_preview(screen: pygame.Surface, rect: pygame.Rect) -> None:
    size = min(128, rect.width - 60, rect.height // 2)
    board = pygame.Rect(0, 0, size, size)
    board.center = (rect.centerx, rect.top + rect.height // 3)
    pygame.draw.rect(screen, (187, 173, 160), board, border_radius=9)
    gap = 5
    cell = (size - gap * 5) // 4
    values = ((2, 0, 4, 0), (0, 8, 0, 0), (0, 0, 16, 0), (0, 0, 0, 32))
    colors = {
        0: (205, 193, 180),
        2: (238, 228, 218),
        4: (237, 224, 200),
        8: (242, 177, 121),
        16: (245, 149, 99),
        32: (246, 124, 95),
    }
    for row in range(4):
        for column in range(4):
            cell_rect = pygame.Rect(
                board.left + gap + column * (cell + gap),
                board.top + gap + row * (cell + gap),
                cell,
                cell,
            )
            value = values[row][column]
            pygame.draw.rect(screen, colors[value], cell_rect, border_radius=4)
            if value:
                label = get_font(max(14, cell // 2), bold=True).render(
                    str(value), True, (119, 110, 101)
                )
                screen.blit(label, label.get_rect(center=cell_rect.center))
