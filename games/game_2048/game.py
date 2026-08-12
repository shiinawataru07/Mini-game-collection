"""2048 application loop that coordinates rules, animation, storage, and UI."""

from __future__ import annotations

from typing import cast

import pygame

from .animation import MoveAnimation, ScorePopup, animation_tile_scales, build_move_animation
from .config import (
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    FPS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    SCORE_POPUP_MS,
    SLIDE_ANIMATION_MS,
    TEXTS,
    THEMES,
    TILE_EFFECT_ANIMATION_MS,
    TOTAL_MOVE_ANIMATION_MS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    Language,
    text,
)
from .logic import Direction, new_game
from .persistence import (
    create_save_json,
    load_best_score,
    parse_save_json,
    save_best_score,
)
from .ui import (
    copy_to_clipboard,
    draw_game,
    page_layout,
    read_from_clipboard,
    settings_controls,
)

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


def _score_popup(animation: MoveAnimation) -> ScorePopup | None:
    if not animation.gained_score:
        return None
    return ScorePopup(
        animation.gained_score,
        animation.started_at + SLIDE_ANIMATION_MS,
    )


def run() -> None:
    """Start the resizable 2048 game window."""

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Mini Game Collection - 2048")
    clock = pygame.time.Clock()

    state = new_game()
    best_score = load_best_score()
    theme_name = DEFAULT_THEME
    language: Language = DEFAULT_LANGUAGE
    settings_open = False
    settings_notice = ""
    animation: MoveAnimation | None = None
    queued_direction: Direction | None = None
    score_popup: ScorePopup | None = None
    running = True

    while running:
        now = pygame.time.get_ticks()
        if score_popup and now - score_popup.started_at >= SCORE_POPUP_MS:
            score_popup = None

        if animation and now - animation.started_at >= TOTAL_MOVE_ANIMATION_MS:
            state = animation.end_state
            if state.score > best_score:
                best_score = state.score
                save_best_score(best_score)
            animation = None

            if queued_direction is not None:
                direction = queued_direction
                queued_direction = None
                animation = build_move_animation(state, direction, now)
                if animation:
                    score_popup = _score_popup(animation)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(
                    (
                        max(MIN_WINDOW_WIDTH, event.w),
                        max(MIN_WINDOW_HEIGHT, event.h),
                    ),
                    pygame.RESIZABLE,
                )
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if settings_open:
                        settings_open = False
                        settings_notice = ""
                    else:
                        running = False
                elif not settings_open and animation is None and event.key == pygame.K_r:
                    state = new_game()
                    queued_direction = None
                    score_popup = None
                elif not settings_open and event.key in KEY_DIRECTIONS:
                    direction = KEY_DIRECTIONS[event.key]
                    if animation:
                        queued_direction = direction
                    else:
                        animation = build_move_animation(state, direction, now)
                        if animation:
                            score_popup = _score_popup(animation)
                continue

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            if settings_open:
                (
                    _,
                    close,
                    theme_buttons,
                    language_buttons,
                    copy_save,
                    load_save,
                    restart,
                ) = settings_controls(screen.get_size())

                if close.collidepoint(event.pos):
                    settings_open = False
                    settings_notice = ""
                elif restart.collidepoint(event.pos):
                    state = new_game()
                    animation = None
                    queued_direction = None
                    score_popup = None
                    settings_open = False
                    settings_notice = ""
                elif copy_save.collidepoint(event.pos):
                    save_json = create_save_json(state, best_score, theme_name, language)
                    key = "save_copied" if copy_to_clipboard(save_json) else "clipboard_error"
                    settings_notice = text(language, key)
                elif load_save.collidepoint(event.pos):
                    save_json = read_from_clipboard()
                    if save_json is None:
                        settings_notice = text(language, "clipboard_error")
                    else:
                        try:
                            saved = parse_save_json(
                                save_json,
                                allowed_themes=set(THEMES),
                                allowed_languages=set(TEXTS),
                            )
                        except ValueError:
                            settings_notice = text(language, "invalid_save")
                        else:
                            state = saved.state
                            best_score = max(best_score, saved.best_score, state.score)
                            theme_name = saved.theme
                            language = cast(Language, saved.language)
                            animation = None
                            queued_direction = None
                            score_popup = None
                            save_best_score(best_score)
                            settings_notice = text(language, "load_success")
                else:
                    for name, rect in theme_buttons.items():
                        if rect.collidepoint(event.pos):
                            theme_name = name
                            settings_notice = ""
                            break
                    for selected_language, rect in language_buttons.items():
                        if rect.collidepoint(event.pos):
                            language = selected_language
                            settings_notice = ""
                            break
            elif animation is None:
                settings_rect = page_layout(screen.get_size())["settings"]
                if isinstance(settings_rect, pygame.Rect) and settings_rect.collidepoint(event.pos):
                    settings_open = True
                    settings_notice = ""

        if animation:
            elapsed = now - animation.started_at
            if elapsed < SLIDE_ANIMATION_MS:
                draw_game(
                    screen,
                    animation.start_state,
                    theme_name,
                    language=language,
                    motions=animation.motions,
                    animation_progress=max(0.0, elapsed / SLIDE_ANIMATION_MS),
                    best_score=best_score,
                    score_popup=score_popup,
                    current_time=now,
                    show_game_over=False,
                )
            else:
                effect_progress = min(
                    1.0,
                    (elapsed - SLIDE_ANIMATION_MS) / TILE_EFFECT_ANIMATION_MS,
                )
                draw_game(
                    screen,
                    animation.end_state,
                    theme_name,
                    language=language,
                    best_score=best_score,
                    tile_scales=animation_tile_scales(animation, effect_progress),
                    score_popup=score_popup,
                    current_time=now,
                    show_game_over=False,
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
                score_popup=score_popup,
                current_time=now,
            )

        pygame.display.flip()
        clock.tick(FPS)

    save_best_score(best_score)
    pygame.quit()
