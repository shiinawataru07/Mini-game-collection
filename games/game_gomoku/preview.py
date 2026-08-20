"""Menu preview renderer for the wooden Gomoku board."""

import pygame


def draw_preview(screen: pygame.Surface, rect: pygame.Rect) -> None:
    size = min(142, rect.width - 54, rect.height // 2)
    board = pygame.Rect(0, 0, size, size)
    board.center = (rect.centerx, rect.top + rect.height // 3)
    pygame.draw.rect(screen, (190, 139, 76), board, border_radius=7)
    margin = max(10, size // 10)
    spacing = (size - margin * 2) / 8
    for index in range(9):
        coordinate = round(margin + index * spacing)
        pygame.draw.line(
            screen,
            (83, 55, 30),
            (board.left + margin, board.top + coordinate),
            (board.right - margin, board.top + coordinate),
            1,
        )
        pygame.draw.line(
            screen,
            (83, 55, 30),
            (board.left + coordinate, board.top + margin),
            (board.left + coordinate, board.bottom - margin),
            1,
        )
    stones = (
        (2, 3, (27, 27, 26)),
        (3, 4, (239, 235, 220)),
        (4, 4, (27, 27, 26)),
        (5, 5, (239, 235, 220)),
        (6, 5, (27, 27, 26)),
    )
    radius = max(4, round(spacing * 0.42))
    for column, row, color in stones:
        center = (
            round(board.left + margin + column * spacing),
            round(board.top + margin + row * spacing),
        )
        pygame.draw.circle(screen, (88, 58, 31), (center[0] + 1, center[1] + 2), radius)
        pygame.draw.circle(screen, color, center, radius)
