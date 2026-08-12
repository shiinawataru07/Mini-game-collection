"""Pygame layout, drawing, fonts, settings, and clipboard helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import pygame

from .animation import ScorePopup, TileMotion
from .config import (
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    SCORE_POPUP_MS,
    THEMES,
    AiSpeed,
    Color,
    Language,
    Theme,
    text,
)
from .logic import GameState
from .logic import SUPPORTED_BOARD_SIZES


@dataclass(frozen=True)
class SettingsControls:
    modal: pygame.Rect
    close: pygame.Rect
    themes: dict[str, pygame.Rect]
    languages: dict[Language, pygame.Rect]
    board_sizes: dict[int, pygame.Rect]
    ai_speed: pygame.Rect
    copy_save: pygame.Rect
    load_save: pygame.Rect
    restart: pygame.Rect


def copy_to_clipboard(value: str) -> bool:
    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        pygame.scrap.put(pygame.SCRAP_TEXT, value.encode("utf-8") + b"\x00")
        return True
    except pygame.error:
        return False


def read_from_clipboard() -> str | None:
    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        raw = pygame.scrap.get(pygame.SCRAP_TEXT)
        if not raw:
            return None
        return raw.decode("utf-8-sig").rstrip("\x00")
    except (pygame.error, UnicodeDecodeError):
        return None


@lru_cache(maxsize=None)
def _font(
    size: int,
    language: Language = DEFAULT_LANGUAGE,
    bold: bool = False,
) -> pygame.font.Font:
    size = max(16, size)
    font_path = None
    if language == "zh":
        for name in ("microsoftyahei", "simhei", "simsun", "notosanscjksc"):
            font_path = pygame.font.match_font(name)
            if font_path:
                break
    font = pygame.font.Font(font_path, size) if font_path else pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


def page_layout(window_size: tuple[int, int]) -> dict[str, pygame.Rect | int]:
    """Calculate responsive header and board positions."""

    width, height = window_size
    margin = max(14, min(28, min(width, height) // 22))
    board_top = max(158, min(178, height // 5 + 26))
    board_size = max(280, min(width - margin * 2, height - board_top - margin))
    board_left = (width - board_size) // 2
    settings_width = max(92, min(116, width // 4))
    settings = pygame.Rect(width - margin - settings_width, 24, settings_width, 40)
    return {
        "margin": margin,
        "board": pygame.Rect(board_left, board_top, board_size, board_size),
        "settings": settings,
        "ai_toggle": pygame.Rect(settings.left, settings.bottom + 6, settings.width, 38),
    }


def settings_controls(
    window_size: tuple[int, int],
) -> SettingsControls:
    """Calculate the settings dialog and all clickable controls."""

    width, height = window_size
    modal = pygame.Rect(0, 0, min(500, width - 32), min(560, height - 32))
    modal.center = (width // 2, height // 2)
    close = pygame.Rect(modal.right - 48, modal.top + 14, 32, 32)

    theme_buttons = {
        name: pygame.Rect(modal.left + 24, modal.top + 78 + index * 40, modal.width - 48, 36)
        for index, name in enumerate(THEMES)
    }
    language_width = (modal.width - 58) // 2
    language_buttons: dict[Language, pygame.Rect] = {
        "en": pygame.Rect(modal.left + 24, modal.top + 220, language_width, 34),
        "zh": pygame.Rect(
            modal.left + 34 + language_width,
            modal.top + 220,
            language_width,
            34,
        ),
    }
    size_gap = 8
    size_width = (modal.width - 48 - size_gap * 2) // 3
    board_sizes = {
        size: pygame.Rect(
            modal.left + 24 + index * (size_width + size_gap),
            modal.top + 280,
            size_width,
            36,
        )
        for index, size in enumerate(SUPPORTED_BOARD_SIZES)
    }
    ai_speed = pygame.Rect(modal.left + 24, modal.top + 348, modal.width - 48, 36)
    data_width = (modal.width - 58) // 2
    copy_save = pygame.Rect(modal.left + 24, modal.top + 416, data_width, 36)
    load_save = pygame.Rect(modal.left + 34 + data_width, modal.top + 416, data_width, 36)
    restart = pygame.Rect(modal.left + 24, modal.bottom - 54, modal.width - 48, 40)
    return SettingsControls(
        modal,
        close,
        theme_buttons,
        language_buttons,
        board_sizes,
        ai_speed,
        copy_save,
        load_save,
        restart,
    )


def _draw_button(
    screen: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    background: Color,
    foreground: Color,
    font_size: int,
    language: Language,
    border_color: Color | None = None,
) -> None:
    pygame.draw.rect(screen, background, rect, border_radius=8)
    if border_color:
        pygame.draw.rect(screen, border_color, rect, width=3, border_radius=8)
    rendered = _font(font_size, language, bold=True).render(label, True, foreground)
    screen.blit(rendered, rendered.get_rect(center=rect.center))


def _board_geometry(board_rect: pygame.Rect, dimension: int) -> tuple[int, int]:
    gap = max(6, min(12, board_rect.width // 40))
    return gap, (board_rect.width - gap * (dimension + 1)) // dimension


def _cell_rect(
    board_rect: pygame.Rect,
    position: tuple[int, int],
    gap: int,
    cell_size: int,
) -> pygame.Rect:
    row, column = position
    return pygame.Rect(
        board_rect.left + gap + column * (cell_size + gap),
        board_rect.top + gap + row * (cell_size + gap),
        cell_size,
        cell_size,
    )


def _tile_font_size(value: int, cell_size: int) -> int:
    digits = len(str(value))
    if digits <= 2:
        return int(cell_size * 0.43)
    if digits == 3:
        return int(cell_size * 0.36)
    return int(cell_size * 0.29)


def _draw_tile(screen: pygame.Surface, value: int, rect: pygame.Rect, theme: Theme) -> None:
    pygame.draw.rect(screen, theme.tiles.get(value, theme.accent), rect, border_radius=6)
    if rect.width < 28:
        return
    color = theme.text if value <= 4 else theme.light_text
    rendered = _font(_tile_font_size(value, rect.width), "en", bold=True).render(
        str(value), True, color
    )
    screen.blit(rendered, rendered.get_rect(center=rect.center))


def _scaled_rect(rect: pygame.Rect, scale: float) -> pygame.Rect:
    size = max(1, round(rect.width * max(0.0, scale)))
    result = pygame.Rect(0, 0, size, size)
    result.center = rect.center
    return result


def _draw_board(
    screen: pygame.Surface,
    state: GameState,
    theme: Theme,
    board_rect: pygame.Rect,
    language: Language,
    show_tiles: bool,
    tile_scales: dict[tuple[int, int], float] | None,
    show_game_over: bool,
) -> None:
    dimension = len(state.board)
    gap, cell_size = _board_geometry(board_rect, dimension)
    pygame.draw.rect(screen, theme.board, board_rect, border_radius=8)

    for row_index, row in enumerate(state.board):
        for column_index, value in enumerate(row):
            position = (row_index, column_index)
            cell = _cell_rect(board_rect, position, gap, cell_size)
            pygame.draw.rect(screen, theme.empty_cell, cell, border_radius=6)
            if show_tiles and value:
                scale = (tile_scales or {}).get(position, 1.0)
                if scale > 0.01:
                    _draw_tile(screen, value, _scaled_rect(cell, scale), theme)

    if show_tiles and show_game_over and state.game_over:
        overlay = pygame.Surface(board_rect.size, pygame.SRCALPHA)
        overlay.fill((*theme.background, 215))
        screen.blit(overlay, board_rect.topleft)
        title = _font(max(38, board_rect.width // 10), language, bold=True).render(
            text(language, "game_over"), True, theme.text
        )
        restart = _font(max(22, board_rect.width // 20), language).render(
            text(language, "restart_hint"), True, theme.text
        )
        center_x, center_y = board_rect.center
        screen.blit(title, title.get_rect(center=(center_x, center_y - 24)))
        screen.blit(restart, restart.get_rect(center=(center_x, center_y + 28)))


def _draw_moving_tiles(
    screen: pygame.Surface,
    motions: list[TileMotion],
    progress: float,
    theme: Theme,
    board_rect: pygame.Rect,
    dimension: int,
) -> None:
    gap, cell_size = _board_geometry(board_rect, dimension)
    eased = 1 - (1 - progress) ** 3
    for motion in motions:
        start = _cell_rect(board_rect, motion.start, gap, cell_size)
        end = _cell_rect(board_rect, motion.end, gap, cell_size)
        current = pygame.Rect(
            round(start.x + (end.x - start.x) * eased),
            round(start.y + (end.y - start.y) * eased),
            cell_size,
            cell_size,
        )
        _draw_tile(screen, motion.value, current, theme)


def _draw_score_popup(
    screen: pygame.Surface,
    popup: ScorePopup,
    current_time: int,
    score_rect: pygame.Rect,
    settings_rect: pygame.Rect,
    theme: Theme,
) -> None:
    elapsed = current_time - popup.started_at
    if elapsed < 0 or elapsed >= SCORE_POPUP_MS:
        return
    progress = elapsed / SCORE_POPUP_MS
    rendered = _font(22, "en", bold=True).render(f"+{popup.amount}", True, theme.accent)
    rendered.set_alpha(round(255 * (1 - progress)))
    x = min(score_rect.right + 7, settings_rect.left - rendered.get_width() - 7)
    screen.blit(rendered, (x, score_rect.top - round(14 * progress)))


def _draw_settings(
    screen: pygame.Surface,
    selected_theme: str,
    language: Language,
    best_score: int,
    notice: str,
    board_size: int,
    ai_speed: AiSpeed,
) -> None:
    theme = THEMES[selected_theme]
    controls = settings_controls(screen.get_size())
    modal = controls.modal

    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 90))
    screen.blit(shade, (0, 0))
    pygame.draw.rect(screen, theme.background, modal, border_radius=14)
    pygame.draw.rect(screen, theme.board, modal, width=2, border_radius=14)

    title = _font(36, language, bold=True).render(text(language, "settings"), True, theme.text)
    screen.blit(title, (modal.left + 24, modal.top + 14))
    _draw_button(screen, controls.close, "X", theme.empty_cell, theme.text, 24, "en")

    section = _font(21, language, bold=True).render(
        text(language, "color_theme"), True, theme.text
    )
    screen.blit(section, (modal.left + 24, modal.top + 54))
    for name, rect in controls.themes.items():
        option = THEMES[name]
        border = theme.accent if name == selected_theme else theme.board
        pygame.draw.rect(screen, option.background, rect, border_radius=8)
        pygame.draw.rect(
            screen, border, rect, width=3 if name == selected_theme else 1, border_radius=8
        )
        label = _font(19, language, bold=True).render(text(language, name), True, option.text)
        screen.blit(label, (rect.left + 16, rect.centery - label.get_height() // 2))
        preview_left = rect.right - 80
        for index, value in enumerate((2, 8, 64)):
            preview = pygame.Rect(preview_left + index * 25, rect.centery - 10, 20, 20)
            pygame.draw.rect(screen, option.tiles[value], preview, border_radius=4)

    label = _font(21, language, bold=True).render(text(language, "language"), True, theme.text)
    screen.blit(label, (modal.left + 24, modal.top + 195))
    for option_language, rect in controls.languages.items():
        selected = option_language == language
        _draw_button(
            screen,
            rect,
            text(language, "english" if option_language == "en" else "chinese"),
            theme.accent if selected else theme.empty_cell,
            theme.light_text if selected else theme.text,
            18,
            option_language,
            theme.accent,
        )

    size_label = _font(20, language, bold=True).render(
        text(language, "board_size"), True, theme.text
    )
    screen.blit(size_label, (modal.left + 24, modal.top + 257))
    for size, rect in controls.board_sizes.items():
        selected = size == board_size
        _draw_button(
            screen,
            rect,
            f"{size} × {size}",
            theme.accent if selected else theme.empty_cell,
            theme.light_text if selected else theme.text,
            18,
            "en",
            theme.accent,
        )

    ai_label = _font(20, language, bold=True).render(
        text(language, "ai_player"), True, theme.text
    )
    screen.blit(ai_label, (modal.left + 24, modal.top + 325))
    speed_label = text(language, "ai_speed").format(speed=text(language, ai_speed))
    _draw_button(
        screen,
        controls.ai_speed,
        speed_label,
        theme.empty_cell,
        theme.text,
        17,
        language,
        theme.board,
    )

    best = _font(19, language, bold=True).render(
        f"{text(language, 'best_score')}: {best_score}", True, theme.text
    )
    screen.blit(best, (modal.left + 24, modal.top + 390))
    _draw_button(
        screen, controls.copy_save, text(language, "copy_save"), theme.empty_cell,
        theme.text, 17, language, theme.board,
    )
    _draw_button(
        screen, controls.load_save, text(language, "load_save"), theme.empty_cell,
        theme.text, 17, language, theme.board,
    )
    if notice:
        rendered = _font(16, language).render(notice, True, theme.text)
        screen.blit(rendered, (modal.left + 24, modal.top + 456))
    _draw_button(
        screen, controls.restart, text(language, "restart"), theme.accent,
        theme.light_text, 22, language,
    )


def draw_game(
    screen: pygame.Surface,
    state: GameState,
    theme_name: str = DEFAULT_THEME,
    settings_open: bool = False,
    language: Language = DEFAULT_LANGUAGE,
    motions: list[TileMotion] | None = None,
    animation_progress: float = 1.0,
    best_score: int = 0,
    settings_notice: str = "",
    tile_scales: dict[tuple[int, int], float] | None = None,
    score_popup: ScorePopup | None = None,
    current_time: int | None = None,
    show_game_over: bool = True,
    ai_enabled: bool = False,
    ai_speed: AiSpeed = "normal",
    board_size: int | None = None,
) -> None:
    """Render one complete game frame."""

    theme = THEMES[theme_name]
    layout = page_layout(screen.get_size())
    board_rect = layout["board"]
    settings_rect = layout["settings"]
    ai_toggle_rect = layout["ai_toggle"]
    margin = layout["margin"]
    assert isinstance(board_rect, pygame.Rect)
    assert isinstance(settings_rect, pygame.Rect)
    assert isinstance(ai_toggle_rect, pygame.Rect)
    assert isinstance(margin, int)

    screen.fill(theme.background)
    title = _font(64, "en", bold=True).render("2048", True, theme.text)
    screen.blit(title, (margin, 20))
    _draw_button(
        screen, settings_rect, text(language, "settings"), theme.empty_cell,
        theme.text, 22, language, theme.board,
    )
    _draw_button(
        screen,
        ai_toggle_rect,
        text(language, "pause_ai" if ai_enabled else "start_ai"),
        theme.accent if ai_enabled else theme.empty_cell,
        theme.light_text if ai_enabled else theme.text,
        18,
        language,
        theme.accent,
    )

    score = _font(27, language, bold=True).render(
        f"{text(language, 'score')}: {state.score}", True, theme.text
    )
    score_x = min(margin + title.get_width() + 18, settings_rect.left - score.get_width() - 12)
    score_rect = score.get_rect(topleft=(max(margin, score_x), 73))
    screen.blit(score, score_rect)
    if score_popup:
        _draw_score_popup(
            screen,
            score_popup,
            pygame.time.get_ticks() if current_time is None else current_time,
            score_rect,
            settings_rect,
            theme,
        )

    hint = _font(20, language, bold=True).render(text(language, "hint"), True, theme.text)
    screen.blit(hint, (margin, board_rect.top - 27))
    _draw_board(
        screen,
        state,
        theme,
        board_rect,
        language,
        show_tiles=motions is None,
        tile_scales=tile_scales,
        show_game_over=show_game_over,
    )
    if motions is not None:
        _draw_moving_tiles(
            screen, motions, animation_progress, theme, board_rect, len(state.board)
        )
    if settings_open:
        _draw_settings(
            screen,
            theme_name,
            language,
            best_score,
            settings_notice,
            len(state.board) if board_size is None else board_size,
            ai_speed,
        )
