"""Pygame window, input handling, and rendering for 2048."""

from __future__ import annotations

import pygame

from .logic import BOARD_SIZE, Direction, GameState, apply_move, new_game

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 620
BOARD_MARGIN = 24
BOARD_TOP = 120
CELL_GAP = 10
FPS = 60

BACKGROUND_COLOR = (250, 248, 239)
BOARD_COLOR = (187, 173, 160)
EMPTY_CELL_COLOR = (205, 193, 180)
TEXT_DARK = (119, 110, 101)
TEXT_LIGHT = (249, 246, 242)

TILE_COLORS = {
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
}

KEY_DIRECTIONS: dict[int, Direction] = {
    pygame.K_UP: "up",
    pygame.K_w: "up",
    pygame.K_DOWN: "down",
    pygame.K_s: "down",
    pygame.K_LEFT: "left",
    pygame.K_a: "left",
    pygame.K_RIGHT: "right",
    pygame.K_d: "right",
}


def _tile_font_size(value: int, cell_size: int) -> int:
    digits = len(str(value))
    if digits <= 2:
        return int(cell_size * 0.43)
    if digits == 3:
        return int(cell_size * 0.36)
    return int(cell_size * 0.29)


def draw_game(screen: pygame.Surface, state: GameState) -> None:
    """Draw the current state to the Pygame window."""

    screen.fill(BACKGROUND_COLOR)
    title_font = pygame.font.Font(None, 72)
    info_font = pygame.font.Font(None, 34)

    screen.blit(title_font.render("2048", True, TEXT_DARK), (BOARD_MARGIN, 28))
    score_text = info_font.render(f"Score: {state.score}", True, TEXT_DARK)
    screen.blit(score_text, (WINDOW_WIDTH - BOARD_MARGIN - score_text.get_width(), 38))

    hint_font = pygame.font.Font(None, 24)
    hint = hint_font.render("Arrow keys / WASD to move   R to restart", True, TEXT_DARK)
    screen.blit(hint, (BOARD_MARGIN, 92))

    board_size_px = WINDOW_WIDTH - BOARD_MARGIN * 2
    cell_size = (board_size_px - CELL_GAP * (BOARD_SIZE + 1)) // BOARD_SIZE
    board_rect = pygame.Rect(BOARD_MARGIN, BOARD_TOP, board_size_px, board_size_px)
    pygame.draw.rect(screen, BOARD_COLOR, board_rect, border_radius=8)

    for row_index, row in enumerate(state.board):
        for column_index, value in enumerate(row):
            x = BOARD_MARGIN + CELL_GAP + column_index * (cell_size + CELL_GAP)
            y = BOARD_TOP + CELL_GAP + row_index * (cell_size + CELL_GAP)
            cell_rect = pygame.Rect(x, y, cell_size, cell_size)
            color = TILE_COLORS.get(value, (60, 58, 50)) if value else EMPTY_CELL_COLOR
            pygame.draw.rect(screen, color, cell_rect, border_radius=6)

            if value:
                text_color = TEXT_DARK if value <= 4 else TEXT_LIGHT
                tile_font = pygame.font.Font(None, _tile_font_size(value, cell_size))
                tile_text = tile_font.render(str(value), True, text_color)
                screen.blit(tile_text, tile_text.get_rect(center=cell_rect.center))

    if state.game_over:
        overlay = pygame.Surface((board_size_px, board_size_px), pygame.SRCALPHA)
        overlay.fill((238, 228, 218, 205))
        screen.blit(overlay, board_rect.topleft)

        over_font = pygame.font.Font(None, 58)
        restart_font = pygame.font.Font(None, 30)
        over_text = over_font.render("Game Over", True, TEXT_DARK)
        restart_text = restart_font.render("Press R to restart", True, TEXT_DARK)
        center_x, center_y = board_rect.center
        screen.blit(over_text, over_text.get_rect(center=(center_x, center_y - 24)))
        screen.blit(restart_text, restart_text.get_rect(center=(center_x, center_y + 28)))


def run() -> None:
    """Start the 2048 game loop."""

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Mini Game Collection - 2048")
    clock = pygame.time.Clock()
    state = new_game()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    state = new_game()
                elif event.key in KEY_DIRECTIONS:
                    state = apply_move(state, KEY_DIRECTIONS[event.key])

        draw_game(screen, state)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

