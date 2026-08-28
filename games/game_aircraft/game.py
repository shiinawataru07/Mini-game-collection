"""Application loop for Pixel Aircraft Battle."""

from __future__ import annotations

import random

import pygame

from games.common.app_settings import handle_global_shortcut, load_app_settings
from games.common.types import Navigation
from games.common.window import open_resizable_window, resize_resizable_window

from .config import FIXED_STEP_MS, FPS, MIN_WINDOW_SIZE, WINDOW_SIZE
from .logic import CraftKind, advance, new_game, start, toggle_pause
from .persistence import load_best_score, save_best_score
from .sound import GameSounds
from .ui import craft_controls, draw_game

MOVE_KEYS = {
    "left": (pygame.K_LEFT, pygame.K_a),
    "right": (pygame.K_RIGHT, pygame.K_d),
    "up": (pygame.K_UP, pygame.K_w),
    "down": (pygame.K_DOWN, pygame.K_s),
}
CRAFT_KEYS: dict[int, CraftKind] = {
    pygame.K_1: "falcon",
    pygame.K_KP1: "falcon",
    pygame.K_2: "viper",
    pygame.K_KP2: "viper",
    pygame.K_3: "guardian",
    pygame.K_KP3: "guardian",
}


def _movement() -> tuple[float, float]:
    pressed = pygame.key.get_pressed()
    left = any(pressed[key] for key in MOVE_KEYS["left"])
    right = any(pressed[key] for key in MOVE_KEYS["right"])
    up = any(pressed[key] for key in MOVE_KEYS["up"])
    down = any(pressed[key] for key in MOVE_KEYS["down"])
    return (float(right) - float(left), float(down) - float(up))


def run() -> Navigation:
    """Run the shooter until the player returns to the collection or quits."""

    app_settings = load_app_settings()
    screen = open_resizable_window(
        WINDOW_SIZE,
        "Mini Game Collection - Pixel Striker",
        app_settings.fullscreen,
    )
    clock = pygame.time.Clock()
    sounds = GameSounds(app_settings)
    rng = random.Random()
    state = new_game()
    selecting_craft = True
    best_score = load_best_score()
    accumulator = 0.0
    navigation: Navigation = "menu"
    running = True

    while running:
        elapsed_ms = clock.tick(FPS)
        layout = draw_game(screen, state, best_score, selecting_craft)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                navigation = "quit"
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = resize_resizable_window((event.w, event.h), MIN_WINDOW_SIZE)
            elif event.type == pygame.KEYDOWN:
                handled = handle_global_shortcut(event.key, app_settings, MIN_WINDOW_SIZE)
                if handled is not None:
                    app_settings, screen = handled
                    sounds.update_settings(app_settings)
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif selecting_craft and event.key in CRAFT_KEYS:
                    state = start(new_game(CRAFT_KEYS[event.key]))
                    selecting_craft = False
                    accumulator = 0.0
                elif selecting_craft:
                    continue
                elif event.key == pygame.K_c:
                    selecting_craft = True
                    accumulator = 0.0
                elif event.key == pygame.K_r:
                    state = start(new_game(state.player.craft))
                    accumulator = 0.0
                elif event.key == pygame.K_p:
                    state = toggle_pause(state)
                    accumulator = 0.0
                elif event.key == pygame.K_SPACE:
                    if state.status == "game_over":
                        state = start(new_game(state.player.craft))
                    else:
                        state = start(state)
                    accumulator = 0.0
                elif event.key in (
                    *MOVE_KEYS["left"],
                    *MOVE_KEYS["right"],
                    *MOVE_KEYS["up"],
                    *MOVE_KEYS["down"],
                ):
                    state = start(state)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if selecting_craft:
                    controls = craft_controls(screen.get_size())
                    selected = next(
                        (
                            craft
                            for craft, rect in controls.cards.items()
                            if rect.collidepoint(event.pos)
                        ),
                        None,
                    )
                    if selected is not None:
                        state = start(new_game(selected))
                        selecting_craft = False
                        accumulator = 0.0
                elif layout.back.collidepoint(event.pos):
                    running = False
                elif layout.restart.collidepoint(event.pos):
                    state = start(new_game(state.player.craft))
                    accumulator = 0.0
                elif layout.pause.collidepoint(event.pos):
                    state = start(state) if state.status == "ready" else toggle_pause(state)
                    accumulator = 0.0

        if not running:
            continue
        if state.status == "running" and not selecting_craft:
            accumulator += min(250.0, elapsed_ms)
            movement = _movement()
            while accumulator >= FIXED_STEP_MS and state.status == "running":
                accumulator -= FIXED_STEP_MS
                transition = advance(state, FIXED_STEP_MS, movement, rng)
                state = transition.state
                sounds.play_transition(transition)
                if state.score > best_score:
                    best_score = state.score
        else:
            accumulator = 0.0

    save_best_score(best_score)
    return navigation
