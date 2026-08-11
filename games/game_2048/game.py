"""Pygame window, settings, input handling, and rendering for 2048."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from .logic import Direction, GameState, apply_move, new_game

Color = tuple[int, int, int]

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 620
MIN_WINDOW_WIDTH = 360
MIN_WINDOW_HEIGHT = 500
FPS = 60
DEFAULT_THEME = "warm"


@dataclass(frozen=True)
class Theme:
    """Colors used to render one visual theme."""

    name: str
    background: Color
    board: Color
    empty_cell: Color
    text: Color
    light_text: Color
    accent: Color
    tiles: dict[int, Color]


THEMES: dict[str, Theme] = {
    "warm": Theme(
        name="Warm",
        background=(250, 248, 239),
        board=(187, 173, 160),
        empty_cell=(205, 193, 180),
        text=(119, 110, 101),
        light_text=(249, 246, 242),
        accent=(143, 122, 102),
        tiles={
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
        },
    ),
    "blue": Theme(
        name="Light Blue",
        background=(241, 247, 252),
        board=(156, 180, 201),
        empty_cell=(202, 217, 229),
        text=(61, 79, 94),
        light_text=(247, 251, 255),
        accent=(74, 139, 193),
        tiles={
            2: (222, 237, 247),
            4: (203, 227, 243),
            8: (163, 210, 239),
            16: (121, 190, 232),
            32: (83, 169, 222),
            64: (50, 146, 207),
            128: (96, 173, 196),
            256: (73, 154, 181),
            512: (53, 134, 164),
            1024: (37, 113, 143),
            2048: (24, 92, 122),
        },
    ),
    "green": Theme(
        name="Light Green",
        background=(243, 249, 243),
        board=(157, 184, 160),
        empty_cell=(207, 222, 207),
        text=(60, 83, 62),
        light_text=(248, 252, 248),
        accent=(82, 145, 91),
        tiles={
            2: (225, 239, 225),
            4: (208, 232, 209),
            8: (174, 216, 177),
            16: (139, 198, 145),
            32: (105, 180, 113),
            64: (76, 159, 86),
            128: (129, 184, 126),
            256: (105, 163, 104),
            512: (82, 143, 84),
            1024: (61, 122, 66),
            2048: (43, 101, 50),
        },
    ),
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


def _font(size: int) -> pygame.font.Font:
    return pygame.font.Font(None, max(16, size))


def _tile_font_size(value: int, cell_size: int) -> int:
    digits = len(str(value))
    if digits <= 2:
        return int(cell_size * 0.43)
    if digits == 3:
        return int(cell_size * 0.36)
    return int(cell_size * 0.29)


def _page_layout(window_size: tuple[int, int]) -> dict[str, pygame.Rect | int]:
    """Calculate responsive header and board positions."""

    width, height = window_size
    margin = max(14, min(28, min(width, height) // 22))
    board_top = max(120, min(145, height // 5 + 12))
    board_size = min(width - margin * 2, height - board_top - margin)
    board_size = max(280, board_size)
    board_left = (width - board_size) // 2
    settings_width = max(92, min(116, width // 4))

    return {
        "margin": margin,
        "board": pygame.Rect(board_left, board_top, board_size, board_size),
        "settings": pygame.Rect(width - margin - settings_width, 24, settings_width, 40),
    }


def _settings_controls(
    window_size: tuple[int, int],
) -> tuple[pygame.Rect, pygame.Rect, dict[str, pygame.Rect], pygame.Rect]:
    """Calculate the settings dialog and its clickable controls."""

    width, height = window_size
    modal_width = min(420, width - 32)
    modal_height = min(440, height - 32)
    modal = pygame.Rect(0, 0, modal_width, modal_height)
    modal.center = (width // 2, height // 2)

    close = pygame.Rect(modal.right - 48, modal.top + 14, 32, 32)
    theme_buttons: dict[str, pygame.Rect] = {}
    button_top = modal.top + 105
    button_height = 54
    button_gap = 10
    for index, theme_name in enumerate(THEMES):
        theme_buttons[theme_name] = pygame.Rect(
            modal.left + 24,
            button_top + index * (button_height + button_gap),
            modal.width - 48,
            button_height,
        )

    restart = pygame.Rect(modal.left + 24, modal.bottom - 68, modal.width - 48, 44)
    return modal, close, theme_buttons, restart


def _draw_button(
    screen: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    background: Color,
    foreground: Color,
    font_size: int = 26,
    border_color: Color | None = None,
) -> None:
    pygame.draw.rect(screen, background, rect, border_radius=8)
    if border_color:
        pygame.draw.rect(screen, border_color, rect, width=3, border_radius=8)
    text = _font(font_size).render(label, True, foreground)
    screen.blit(text, text.get_rect(center=rect.center))


def _draw_board(
    screen: pygame.Surface,
    state: GameState,
    theme: Theme,
    board_rect: pygame.Rect,
) -> None:
    board_dimension = len(state.board)
    gap = max(6, min(12, board_rect.width // 40))
    cell_size = (board_rect.width - gap * (board_dimension + 1)) // board_dimension
    pygame.draw.rect(screen, theme.board, board_rect, border_radius=8)

    for row_index, row in enumerate(state.board):
        for column_index, value in enumerate(row):
            x = board_rect.left + gap + column_index * (cell_size + gap)
            y = board_rect.top + gap + row_index * (cell_size + gap)
            cell_rect = pygame.Rect(x, y, cell_size, cell_size)
            color = theme.tiles.get(value, theme.accent) if value else theme.empty_cell
            pygame.draw.rect(screen, color, cell_rect, border_radius=6)

            if value:
                text_color = theme.text if value <= 4 else theme.light_text
                tile_text = _font(_tile_font_size(value, cell_size)).render(
                    str(value), True, text_color
                )
                screen.blit(tile_text, tile_text.get_rect(center=cell_rect.center))

    if state.game_over:
        overlay = pygame.Surface(board_rect.size, pygame.SRCALPHA)
        overlay.fill((*theme.background, 215))
        screen.blit(overlay, board_rect.topleft)

        title = _font(max(42, board_rect.width // 9)).render("Game Over", True, theme.text)
        restart = _font(max(24, board_rect.width // 18)).render(
            "Press R to restart", True, theme.text
        )
        center_x, center_y = board_rect.center
        screen.blit(title, title.get_rect(center=(center_x, center_y - 24)))
        screen.blit(restart, restart.get_rect(center=(center_x, center_y + 28)))


def _draw_settings(
    screen: pygame.Surface,
    selected_theme: str,
    theme: Theme,
) -> None:
    window_size = screen.get_size()
    modal, close, theme_buttons, restart = _settings_controls(window_size)

    shade = pygame.Surface(window_size, pygame.SRCALPHA)
    shade.fill((0, 0, 0, 90))
    screen.blit(shade, (0, 0))

    pygame.draw.rect(screen, theme.background, modal, border_radius=14)
    pygame.draw.rect(screen, theme.board, modal, width=2, border_radius=14)

    title = _font(42).render("Settings", True, theme.text)
    screen.blit(title, (modal.left + 24, modal.top + 22))
    _draw_button(screen, close, "X", theme.empty_cell, theme.text, 24)

    section_title = _font(24).render("Color theme", True, theme.text)
    screen.blit(section_title, (modal.left + 24, modal.top + 78))

    for theme_name, rect in theme_buttons.items():
        option = THEMES[theme_name]
        border = theme.accent if theme_name == selected_theme else theme.board
        pygame.draw.rect(screen, option.background, rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, width=3 if theme_name == selected_theme else 1, border_radius=8)

        label = _font(25).render(option.name, True, option.text)
        screen.blit(label, (rect.left + 16, rect.centery - label.get_height() // 2))

        preview_size = 24
        preview_gap = 5
        preview_left = rect.right - 3 * preview_size - 2 * preview_gap - 14
        for index, tile_value in enumerate((2, 8, 64)):
            preview = pygame.Rect(
                preview_left + index * (preview_size + preview_gap),
                rect.centery - preview_size // 2,
                preview_size,
                preview_size,
            )
            pygame.draw.rect(screen, option.tiles[tile_value], preview, border_radius=4)

    _draw_button(
        screen,
        restart,
        "Restart game",
        theme.accent,
        theme.light_text,
        27,
    )


def draw_game(
    screen: pygame.Surface,
    state: GameState,
    theme_name: str = DEFAULT_THEME,
    settings_open: bool = False,
) -> None:
    """Draw the current state and optional settings dialog."""

    theme = THEMES[theme_name]
    layout = _page_layout(screen.get_size())
    board_rect = layout["board"]
    settings_rect = layout["settings"]
    margin = layout["margin"]
    assert isinstance(board_rect, pygame.Rect)
    assert isinstance(settings_rect, pygame.Rect)
    assert isinstance(margin, int)

    screen.fill(theme.background)
    title = _font(64).render("2048", True, theme.text)
    screen.blit(title, (margin, 20))

    _draw_button(
        screen,
        settings_rect,
        "Settings",
        theme.empty_cell,
        theme.text,
        24,
        theme.board,
    )

    score = _font(29).render(f"Score: {state.score}", True, theme.text)
    score_x = min(margin + title.get_width() + 18, settings_rect.left - score.get_width() - 12)
    screen.blit(score, (max(margin, score_x), 73))

    hint = _font(21).render("Arrow keys / WASD to move   R to restart", True, theme.text)
    screen.blit(hint, (margin, board_rect.top - 27))

    _draw_board(screen, state, theme, board_rect)

    if settings_open:
        _draw_settings(screen, theme_name, theme)


def run() -> None:
    """Start the resizable 2048 game window."""

    pygame.init()
    screen = pygame.display.set_mode(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
        pygame.RESIZABLE,
    )
    pygame.display.set_caption("Mini Game Collection - 2048")
    clock = pygame.time.Clock()
    state = new_game()
    theme_name = DEFAULT_THEME
    settings_open = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(
                    (
                        max(MIN_WINDOW_WIDTH, event.w),
                        max(MIN_WINDOW_HEIGHT, event.h),
                    ),
                    pygame.RESIZABLE,
                )
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if settings_open:
                        settings_open = False
                    else:
                        running = False
                elif not settings_open and event.key == pygame.K_r:
                    state = new_game()
                elif not settings_open and event.key in KEY_DIRECTIONS:
                    state = apply_move(state, KEY_DIRECTIONS[event.key])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if settings_open:
                    _, close, theme_buttons, restart = _settings_controls(screen.get_size())
                    if close.collidepoint(event.pos):
                        settings_open = False
                    elif restart.collidepoint(event.pos):
                        state = new_game()
                        settings_open = False
                    else:
                        for option_name, rect in theme_buttons.items():
                            if rect.collidepoint(event.pos):
                                theme_name = option_name
                                break
                else:
                    layout = _page_layout(screen.get_size())
                    settings_rect = layout["settings"]
                    if isinstance(settings_rect, pygame.Rect) and settings_rect.collidepoint(event.pos):
                        settings_open = True

        draw_game(screen, state, theme_name, settings_open)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

