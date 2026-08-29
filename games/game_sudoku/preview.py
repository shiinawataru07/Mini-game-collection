"""Collection-menu preview for Sudoku."""

import pygame

from games.common.fonts import get_font


def draw_preview(screen: pygame.Surface, rect: pygame.Rect) -> None:
    size = min(148, rect.width - 50, rect.height // 2)
    board = pygame.Rect(0, 0, size, size)
    board.center = (rect.centerx, rect.top + rect.height // 3)
    pygame.draw.rect(screen, (252, 253, 250), board, border_radius=5)
    cell = size / 9
    for index in range(10):
        coordinate = round(index * cell)
        width = 2 if index % 3 == 0 else 1
        color = (64, 91, 88) if width == 2 else (190, 204, 199)
        pygame.draw.line(
            screen,
            color,
            (board.left + coordinate, board.top),
            (board.left + coordinate, board.bottom),
            width,
        )
        pygame.draw.line(
            screen,
            color,
            (board.left, board.top + coordinate),
            (board.right, board.top + coordinate),
            width,
        )
    givens = ((0, 0, 5), (3, 0, 7), (7, 1, 4), (1, 3, 6), (4, 4, 5), (8, 5, 3), (2, 7, 7), (6, 8, 9))
    font = get_font(max(10, round(cell * 0.68)), "en", bold=True)
    for column, row, value in givens:
        rendered = font.render(str(value), True, (43, 69, 66))
        center = (
            round(board.left + (column + 0.5) * cell),
            round(board.top + (row + 0.5) * cell),
        )
        screen.blit(rendered, rendered.get_rect(center=center))
