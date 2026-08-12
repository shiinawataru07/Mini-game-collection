"""Pygame window, settings, animation, input, and rendering for 2048."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import pygame

from .logic import (
    Direction,
    GameState,
    apply_move,
    create_save_json,
    new_game,
    parse_save_json,
)

Color = tuple[int, int, int]
Language = Literal["en", "zh"]

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 620
MIN_WINDOW_WIDTH = 360
MIN_WINDOW_HEIGHT = 500
FPS = 60
MOVE_ANIMATION_MS = 110
DEFAULT_THEME = "warm"
DEFAULT_LANGUAGE: Language = "en"
PLAYER_DATA_PATH = Path(__file__).with_name(".player_data.json")


@dataclass(frozen=True)
class Theme:
    """Colors used to render one visual theme."""

    background: Color
    board: Color
    empty_cell: Color
    text: Color
    light_text: Color
    accent: Color
    tiles: dict[int, Color]


@dataclass(frozen=True)
class TileMotion:
    """One tile moving between two board coordinates."""

    value: int
    start: tuple[int, int]
    end: tuple[int, int]


@dataclass(frozen=True)
class MoveAnimation:
    """Runtime information for one short move animation."""

    start_state: GameState
    end_state: GameState
    motions: list[TileMotion]
    started_at: int


THEMES: dict[str, Theme] = {
    "warm": Theme(
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

TEXTS: dict[Language, dict[str, str]] = {
    "en": {
        "settings": "Settings",
        "score": "Score",
        "hint": "Arrow keys / WASD to move   R to restart",
        "game_over": "Game Over",
        "restart_hint": "Press R to restart",
        "color_theme": "Color theme",
        "language": "Language",
        "warm": "Warm",
        "blue": "Light Blue",
        "green": "Light Green",
        "english": "English",
        "chinese": "中文",
        "restart": "Restart game",
        "best_score": "Best score",
        "copy_save": "Copy save JSON",
        "load_save": "Load JSON",
        "save_copied": "Save JSON copied to clipboard",
        "load_success": "Save loaded successfully",
        "invalid_save": "Invalid save JSON",
        "clipboard_error": "Clipboard is unavailable",
    },
    "zh": {
        "settings": "设置",
        "score": "分数",
        "hint": "方向键 / WASD 移动    R 重新开始",
        "game_over": "游戏结束",
        "restart_hint": "按 R 重新开始",
        "color_theme": "颜色主题",
        "language": "语言",
        "warm": "暖橙色",
        "blue": "淡蓝色",
        "green": "淡绿色",
        "english": "English",
        "chinese": "中文",
        "restart": "重新开始游戏",
        "best_score": "历史最佳分数",
        "copy_save": "复制存档 JSON",
        "load_save": "读取 JSON",
        "save_copied": "存档 JSON 已复制到剪贴板",
        "load_success": "读档成功",
        "invalid_save": "存档 JSON 无效",
        "clipboard_error": "无法访问剪贴板",
    },
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


def _text(language: Language, key: str) -> str:
    return TEXTS[language][key]


def load_best_score(path: Path = PLAYER_DATA_PATH) -> int:
    """Load the locally persisted best score, returning zero if unavailable."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        score = payload.get("best_score")
        if isinstance(score, int) and not isinstance(score, bool) and score >= 0:
            return score
    except (OSError, json.JSONDecodeError, AttributeError):
        pass
    return 0


def save_best_score(score: int, path: Path = PLAYER_DATA_PATH) -> bool:
    """Persist the best score without interrupting the game on I/O errors."""

    try:
        path.write_text(
            json.dumps({"best_score": max(0, score)}, indent=2),
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def _copy_to_clipboard(text: str) -> bool:
    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8") + b"\x00")
        return True
    except pygame.error:
        return False


def _read_from_clipboard() -> str | None:
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
def _font(size: int, language: Language = DEFAULT_LANGUAGE, bold: bool = False) -> pygame.font.Font:
    """Return a cached font, preferring an installed Chinese font when needed."""

    size = max(16, size)
    font_path = None
    if language == "zh":
        for font_name in ("microsoftyahei", "simhei", "simsun", "notosanscjksc"):
            font_path = pygame.font.match_font(font_name)
            if font_path:
                break

    font = pygame.font.Font(font_path, size) if font_path else pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


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
) -> tuple[
    pygame.Rect,
    pygame.Rect,
    dict[str, pygame.Rect],
    dict[Language, pygame.Rect],
    pygame.Rect,
    pygame.Rect,
    pygame.Rect,
]:
    """Calculate the settings dialog and its clickable controls."""

    width, height = window_size
    modal_width = min(420, width - 32)
    modal_height = min(480, height - 32)
    modal = pygame.Rect(0, 0, modal_width, modal_height)
    modal.center = (width // 2, height // 2)

    close = pygame.Rect(modal.right - 48, modal.top + 14, 32, 32)
    theme_buttons: dict[str, pygame.Rect] = {}
    theme_top = modal.top + 88
    button_height = 42
    button_gap = 6
    for index, theme_name in enumerate(THEMES):
        theme_buttons[theme_name] = pygame.Rect(
            modal.left + 24,
            theme_top + index * (button_height + button_gap),
            modal.width - 48,
            button_height,
        )

    language_gap = 10
    language_width = (modal.width - 58) // 2
    language_buttons: dict[Language, pygame.Rect] = {
        "en": pygame.Rect(modal.left + 24, modal.top + 262, language_width, 38),
        "zh": pygame.Rect(
            modal.left + 24 + language_width + language_gap,
            modal.top + 262,
            language_width,
            38,
        ),
    }
    data_button_width = (modal.width - 58) // 2
    copy_save = pygame.Rect(modal.left + 24, modal.top + 335, data_button_width, 38)
    load_save = pygame.Rect(
        modal.left + 24 + data_button_width + 10,
        modal.top + 335,
        data_button_width,
        38,
    )
    restart = pygame.Rect(modal.left + 24, modal.bottom - 58, modal.width - 48, 42)
    return (
        modal,
        close,
        theme_buttons,
        language_buttons,
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
    cell_size = (board_rect.width - gap * (dimension + 1)) // dimension
    return gap, cell_size


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


def _draw_tile(screen: pygame.Surface, value: int, rect: pygame.Rect, theme: Theme) -> None:
    color = theme.tiles.get(value, theme.accent)
    pygame.draw.rect(screen, color, rect, border_radius=6)
    text_color = theme.text if value <= 4 else theme.light_text
    rendered = _font(_tile_font_size(value, rect.width), "en", bold=True).render(
        str(value), True, text_color
    )
    screen.blit(rendered, rendered.get_rect(center=rect.center))


def _draw_board(
    screen: pygame.Surface,
    state: GameState,
    theme: Theme,
    board_rect: pygame.Rect,
    language: Language,
    show_tiles: bool = True,
) -> None:
    dimension = len(state.board)
    gap, cell_size = _board_geometry(board_rect, dimension)
    pygame.draw.rect(screen, theme.board, board_rect, border_radius=8)

    for row_index, row in enumerate(state.board):
        for column_index, value in enumerate(row):
            cell = _cell_rect(board_rect, (row_index, column_index), gap, cell_size)
            pygame.draw.rect(screen, theme.empty_cell, cell, border_radius=6)
            if show_tiles and value:
                _draw_tile(screen, value, cell, theme)

    if show_tiles and state.game_over:
        overlay = pygame.Surface(board_rect.size, pygame.SRCALPHA)
        overlay.fill((*theme.background, 215))
        screen.blit(overlay, board_rect.topleft)

        title = _font(
            max(38, board_rect.width // 10), language, bold=True
        ).render(_text(language, "game_over"), True, theme.text)
        restart = _font(
            max(22, board_rect.width // 20), language
        ).render(_text(language, "restart_hint"), True, theme.text)
        center_x, center_y = board_rect.center
        screen.blit(title, title.get_rect(center=(center_x, center_y - 24)))
        screen.blit(restart, restart.get_rect(center=(center_x, center_y + 28)))


def _line_coordinates(
    dimension: int, direction: Direction, line_index: int
) -> list[tuple[int, int]]:
    """Return one line ordered from the movement edge to the far edge."""

    if direction == "left":
        return [(line_index, column) for column in range(dimension)]
    if direction == "right":
        return [(line_index, column) for column in range(dimension - 1, -1, -1)]
    if direction == "up":
        return [(row, line_index) for row in range(dimension)]
    return [(row, line_index) for row in range(dimension - 1, -1, -1)]


def build_tile_motions(board: list[list[int]], direction: Direction) -> list[TileMotion]:
    """Map every existing tile to its destination for a move animation."""

    dimension = len(board)
    motions: list[TileMotion] = []

    for line_index in range(dimension):
        coordinates = _line_coordinates(dimension, direction, line_index)
        sources = [
            (position, board[position[0]][position[1]])
            for position in coordinates
            if board[position[0]][position[1]]
        ]
        source_index = 0
        target_index = 0

        while source_index < len(sources):
            start, value = sources[source_index]
            destination = coordinates[target_index]
            motions.append(TileMotion(value, start, destination))

            if (
                source_index + 1 < len(sources)
                and value == sources[source_index + 1][1]
            ):
                second_start, second_value = sources[source_index + 1]
                motions.append(TileMotion(second_value, second_start, destination))
                source_index += 2
            else:
                source_index += 1
            target_index += 1

    return motions


def _draw_moving_tiles(
    screen: pygame.Surface,
    motions: list[TileMotion],
    progress: float,
    theme: Theme,
    board_rect: pygame.Rect,
    dimension: int,
) -> None:
    gap, cell_size = _board_geometry(board_rect, dimension)
    eased_progress = 1 - (1 - progress) ** 3

    for motion in motions:
        start = _cell_rect(board_rect, motion.start, gap, cell_size)
        end = _cell_rect(board_rect, motion.end, gap, cell_size)
        current = pygame.Rect(
            round(start.x + (end.x - start.x) * eased_progress),
            round(start.y + (end.y - start.y) * eased_progress),
            cell_size,
            cell_size,
        )
        _draw_tile(screen, motion.value, current, theme)


def _draw_settings(
    screen: pygame.Surface,
    selected_theme: str,
    language: Language,
    theme: Theme,
    best_score: int,
    notice: str,
) -> None:
    window_size = screen.get_size()
    (
        modal,
        close,
        theme_buttons,
        language_buttons,
        copy_save,
        load_save,
        restart,
    ) = _settings_controls(window_size)

    shade = pygame.Surface(window_size, pygame.SRCALPHA)
    shade.fill((0, 0, 0, 90))
    screen.blit(shade, (0, 0))

    pygame.draw.rect(screen, theme.background, modal, border_radius=14)
    pygame.draw.rect(screen, theme.board, modal, width=2, border_radius=14)

    title = _font(36, language, bold=True).render(
        _text(language, "settings"), True, theme.text
    )
    screen.blit(title, (modal.left + 24, modal.top + 14))
    _draw_button(screen, close, "X", theme.empty_cell, theme.text, 24, "en")

    theme_title = _font(21, language, bold=True).render(
        _text(language, "color_theme"), True, theme.text
    )
    screen.blit(theme_title, (modal.left + 24, modal.top + 61))

    for theme_name, rect in theme_buttons.items():
        option = THEMES[theme_name]
        border = theme.accent if theme_name == selected_theme else theme.board
        pygame.draw.rect(screen, option.background, rect, border_radius=8)
        pygame.draw.rect(
            screen,
            border,
            rect,
            width=3 if theme_name == selected_theme else 1,
            border_radius=8,
        )

        label = _font(21, language, bold=True).render(
            _text(language, theme_name), True, option.text
        )
        screen.blit(label, (rect.left + 16, rect.centery - label.get_height() // 2))

        preview_size = 20
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

    language_title = _font(21, language, bold=True).render(
        _text(language, "language"), True, theme.text
    )
    screen.blit(language_title, (modal.left + 24, modal.top + 235))

    for option_language, rect in language_buttons.items():
        selected = option_language == language
        _draw_button(
            screen,
            rect,
            _text(language, "english" if option_language == "en" else "chinese"),
            theme.empty_cell if not selected else theme.accent,
            theme.text if not selected else theme.light_text,
            20,
            option_language,
            theme.accent,
        )

    best = _font(21, language, bold=True).render(
        f"{_text(language, 'best_score')}: {best_score}", True, theme.text
    )
    screen.blit(best, (modal.left + 24, modal.top + 306))

    _draw_button(
        screen,
        copy_save,
        _text(language, "copy_save"),
        theme.empty_cell,
        theme.text,
        18,
        language,
        theme.board,
    )
    _draw_button(
        screen,
        load_save,
        _text(language, "load_save"),
        theme.empty_cell,
        theme.text,
        18,
        language,
        theme.board,
    )

    if notice:
        rendered_notice = _font(17, language).render(notice, True, theme.text)
        screen.blit(rendered_notice, (modal.left + 24, modal.top + 378))

    _draw_button(
        screen,
        restart,
        _text(language, "restart"),
        theme.accent,
        theme.light_text,
        23,
        language,
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
) -> None:
    """Draw the current game, optional movement, and settings dialog."""

    theme = THEMES[theme_name]
    layout = _page_layout(screen.get_size())
    board_rect = layout["board"]
    settings_rect = layout["settings"]
    margin = layout["margin"]
    assert isinstance(board_rect, pygame.Rect)
    assert isinstance(settings_rect, pygame.Rect)
    assert isinstance(margin, int)

    screen.fill(theme.background)
    title = _font(64, "en", bold=True).render("2048", True, theme.text)
    screen.blit(title, (margin, 20))

    _draw_button(
        screen,
        settings_rect,
        _text(language, "settings"),
        theme.empty_cell,
        theme.text,
        22,
        language,
        theme.board,
    )

    score = _font(27, language, bold=True).render(
        f"{_text(language, 'score')}: {state.score}", True, theme.text
    )
    score_x = min(margin + title.get_width() + 18, settings_rect.left - score.get_width() - 12)
    screen.blit(score, (max(margin, score_x), 73))

    hint = _font(20, language, bold=True).render(
        _text(language, "hint"), True, theme.text
    )
    screen.blit(hint, (margin, board_rect.top - 27))

    _draw_board(
        screen,
        state,
        theme,
        board_rect,
        language,
        show_tiles=motions is None,
    )
    if motions is not None:
        _draw_moving_tiles(
            screen,
            motions,
            animation_progress,
            theme,
            board_rect,
            len(state.board),
        )

    if settings_open:
        _draw_settings(
            screen,
            theme_name,
            language,
            theme,
            best_score,
            settings_notice,
        )


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
    best_score = load_best_score()
    theme_name = DEFAULT_THEME
    language = DEFAULT_LANGUAGE
    settings_open = False
    settings_notice = ""
    animation: MoveAnimation | None = None
    running = True

    while running:
        now = pygame.time.get_ticks()
        if animation and now - animation.started_at >= MOVE_ANIMATION_MS:
            state = animation.end_state
            if state.score > best_score:
                best_score = state.score
                save_best_score(best_score)
            animation = None

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
                        settings_notice = ""
                    else:
                        running = False
                elif not settings_open and animation is None and event.key == pygame.K_r:
                    state = new_game()
                elif (
                    not settings_open
                    and animation is None
                    and event.key in KEY_DIRECTIONS
                ):
                    direction = KEY_DIRECTIONS[event.key]
                    next_state = apply_move(state, direction)
                    if next_state.board != state.board:
                        animation = MoveAnimation(
                            start_state=state,
                            end_state=next_state,
                            motions=build_tile_motions(state.board, direction),
                            started_at=pygame.time.get_ticks(),
                        )
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if settings_open:
                    (
                        _,
                        close,
                        theme_buttons,
                        language_buttons,
                        copy_save,
                        load_save,
                        restart,
                    ) = _settings_controls(screen.get_size())
                    if close.collidepoint(event.pos):
                        settings_open = False
                        settings_notice = ""
                    elif restart.collidepoint(event.pos):
                        state = new_game()
                        animation = None
                        settings_open = False
                        settings_notice = ""
                    elif copy_save.collidepoint(event.pos):
                        save_text = create_save_json(
                            state,
                            best_score,
                            theme_name,
                            language,
                        )
                        settings_notice = _text(
                            language,
                            "save_copied" if _copy_to_clipboard(save_text) else "clipboard_error",
                        )
                    elif load_save.collidepoint(event.pos):
                        save_text = _read_from_clipboard()
                        if save_text is None:
                            settings_notice = _text(language, "clipboard_error")
                        else:
                            try:
                                saved = parse_save_json(
                                    save_text,
                                    allowed_themes=set(THEMES),
                                    allowed_languages=set(TEXTS),
                                )
                            except ValueError:
                                settings_notice = _text(language, "invalid_save")
                            else:
                                state = saved.state
                                best_score = max(best_score, saved.best_score, state.score)
                                theme_name = saved.theme
                                language = saved.language
                                animation = None
                                save_best_score(best_score)
                                settings_notice = _text(language, "load_success")
                    else:
                        for option_name, rect in theme_buttons.items():
                            if rect.collidepoint(event.pos):
                                theme_name = option_name
                                settings_notice = ""
                                break
                        for option_language, rect in language_buttons.items():
                            if rect.collidepoint(event.pos):
                                language = option_language
                                settings_notice = ""
                                break
                elif animation is None:
                    layout = _page_layout(screen.get_size())
                    settings_rect = layout["settings"]
                    if (
                        isinstance(settings_rect, pygame.Rect)
                        and settings_rect.collidepoint(event.pos)
                    ):
                        settings_open = True
                        settings_notice = ""

        if animation:
            progress = min(
                1.0,
                (pygame.time.get_ticks() - animation.started_at) / MOVE_ANIMATION_MS,
            )
            draw_game(
                screen,
                animation.start_state,
                theme_name,
                False,
                language,
                animation.motions,
                progress,
                best_score,
            )
        else:
            draw_game(
                screen,
                state,
                theme_name,
                settings_open,
                language,
                best_score=best_score,
                settings_notice=settings_notice,
            )

        pygame.display.flip()
        clock.tick(FPS)

    save_best_score(best_score)
    pygame.quit()
