"""Snake application loop coordinating input, fixed-step rules, UI, and storage."""

from __future__ import annotations

from collections import deque
from dataclasses import replace
from pathlib import Path
from typing import Literal, cast

import pygame

from games.common.app_settings import handle_global_shortcut, load_app_settings
from games.common.types import Navigation
from games.common.window import open_resizable_window, resize_resizable_window

from .config import (
    DEFAULT_LANGUAGE,
    DEFAULT_SPEED,
    DEFAULT_THEME,
    FPS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    SPEEDS,
    TEXTS,
    THEMES,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    Language,
    Speed,
    move_interval_ms,
)
from .logic import (
    Direction,
    GameMode,
    advance,
    change_direction,
    elapse_bonus_timer,
    new_game,
    start_or_turn,
    toggle_pause,
)
from .maps import (
    BUILTIN_MAPS,
    EditorState,
    MapFormatError,
    SnakeMap,
    clear_editor,
    discover_maps,
    editor_to_map,
    export_map,
    import_map_file,
    new_editor,
    set_editor_wall,
    toggle_editor_wall,
)
from .persistence import load_player_data, save_player_data
from .sound import GameSounds
from .ui import (
    draw_game,
    draw_map_editor,
    editor_cell_at,
    map_library_controls,
    mode_controls,
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


def run() -> Navigation:
    """Run Snake until the player returns to the collection menu or quits."""

    app_settings = load_app_settings()
    screen = open_resizable_window(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
        "Mini Game Collection - Snake",
        app_settings.fullscreen,
    )
    clock = pygame.time.Clock()
    sounds = GameSounds(app_settings)

    player_data = load_player_data()
    best_score = player_data.best_score
    theme_name = player_data.theme if player_data.theme in THEMES else DEFAULT_THEME
    language = cast(
        Language, player_data.language if player_data.language in TEXTS else DEFAULT_LANGUAGE
    )
    speed = cast(Speed, player_data.speed if player_data.speed in SPEEDS else DEFAULT_SPEED)
    state = new_game()
    pending_directions: deque[Direction] = deque(maxlen=2)
    accumulator = 0.0
    settings_open = False
    view: Literal["modes", "maps", "editor", "game"] = "modes"
    custom_maps, map_errors = discover_maps()
    available_maps: tuple[SnakeMap, ...] = (*BUILTIN_MAPS, *custom_maps)
    map_page = 0
    map_message = map_errors[0] if map_errors else ""
    editor: EditorState = new_editor()
    editor_dragging = False
    editor_brush_add = True
    last_editor_cell: tuple[int, int] | None = None
    navigation: Navigation = "menu"
    running = True

    def refresh_maps(message: str = "") -> None:
        nonlocal custom_maps, available_maps, map_page, map_message
        custom_maps, errors = discover_maps()
        available_maps = (*BUILTIN_MAPS, *custom_maps)
        page_count = max(1, (len(available_maps) + 5) // 6)
        map_page = min(map_page, page_count - 1)
        map_message = message or (errors[0] if errors else "地图文件列表已刷新")

    def launch_map(game_map: SnakeMap) -> None:
        nonlocal state, view, accumulator, settings_open
        state = new_game(game_map=game_map)
        view = "game"
        settings_open = False
        accumulator = 0.0

    def export_editor_map() -> None:
        nonlocal editor
        try:
            path = export_map(editor_to_map(editor))
            editor = replace(editor, message=f"已导出：{path.name}")
            refresh_maps(editor.message)
        except MapFormatError as error:
            editor = replace(editor, message=str(error))

    def play_editor_map() -> None:
        nonlocal editor
        try:
            launch_map(editor_to_map(editor))
        except MapFormatError as error:
            editor = replace(editor, message=str(error))

    while running:
        elapsed_ms = clock.tick(FPS)
        simulation_elapsed_ms = min(elapsed_ms, 250)
        editor_ui = None
        if view == "editor":
            editor_ui = draw_map_editor(screen, editor, theme_name, language)
            layout = None
        else:
            layout = draw_game(
                screen,
                state,
                best_score,
                theme_name,
                language,
                speed,
                settings_open,
                view == "modes",
                view == "maps",
                available_maps,
                map_page,
                map_message,
            )
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                navigation = "quit"
                running = False
                continue

            if event.type == pygame.VIDEORESIZE:
                screen = resize_resizable_window(
                    (event.w, event.h),
                    (MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT),
                )
                continue

            if event.type == pygame.DROPFILE and view == "maps":
                try:
                    imported, destination = import_map_file(Path(event.file))
                    refresh_maps(f"已导入：{imported.name} · {destination.name}")
                except MapFormatError as error:
                    map_message = str(error)
                continue

            if event.type == pygame.TEXTINPUT and view == "editor" and editor.editing_name:
                editor = replace(
                    editor, name=(editor.name + event.text)[:48], message="正在输入名称"
                )
                continue

            if event.type == pygame.KEYDOWN:
                handled = handle_global_shortcut(
                    event.key,
                    app_settings,
                    (MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT),
                )
                if handled is not None:
                    app_settings, screen = handled
                    sounds.update_settings(app_settings)
                elif event.key == pygame.K_ESCAPE:
                    if view == "editor" and editor.editing_name:
                        editor = replace(editor, editing_name=False, message="名称编辑完成")
                        pygame.key.stop_text_input()
                    elif settings_open:
                        settings_open = False
                    elif view == "editor":
                        view = "maps"
                    elif view == "maps":
                        view = "modes"
                    elif view == "modes":
                        running = False
                    else:
                        running = False
                elif view == "editor":
                    if editor.editing_name:
                        if event.key == pygame.K_BACKSPACE:
                            editor = replace(editor, name=editor.name[:-1], message="正在输入名称")
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            editor = replace(editor, editing_name=False, message="名称编辑完成")
                            pygame.key.stop_text_input()
                    elif event.key == pygame.K_n:
                        editor = replace(editor, editing_name=True, message="请输入地图名称")
                        pygame.key.start_text_input()
                    elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                        editor = clear_editor(editor)
                    elif event.key == pygame.K_s and event.mod & pygame.KMOD_CTRL:
                        export_editor_map()
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        play_editor_map()
                elif view == "maps":
                    if event.key in (
                        pygame.K_1,
                        pygame.K_2,
                        pygame.K_3,
                        pygame.K_4,
                        pygame.K_5,
                        pygame.K_6,
                        pygame.K_KP1,
                        pygame.K_KP2,
                        pygame.K_KP3,
                        pygame.K_KP4,
                        pygame.K_KP5,
                        pygame.K_KP6,
                    ):
                        key_index = (
                            event.key - pygame.K_1
                            if pygame.K_1 <= event.key <= pygame.K_6
                            else event.key - pygame.K_KP1
                        )
                        map_index = map_page * 6 + key_index
                        if map_index < len(available_maps):
                            launch_map(available_maps[map_index])
                    elif event.key == pygame.K_e:
                        editor = new_editor()
                        view = "editor"
                    elif event.key == pygame.K_r:
                        refresh_maps()
                    elif event.key == pygame.K_LEFT:
                        map_page = max(0, map_page - 1)
                    elif event.key == pygame.K_RIGHT:
                        page_count = max(1, (len(available_maps) + 5) // 6)
                        map_page = min(page_count - 1, map_page + 1)
                elif view == "modes" and event.key in (
                    pygame.K_1,
                    pygame.K_KP1,
                    pygame.K_2,
                    pygame.K_KP2,
                    pygame.K_3,
                    pygame.K_KP3,
                    pygame.K_4,
                    pygame.K_KP4,
                ):
                    if event.key in (pygame.K_1, pygame.K_KP1):
                        mode: GameMode = "classic"
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        mode = "wrap"
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        mode = "maze"
                    else:
                        view = "maps"
                        continue
                    state = new_game(mode=mode)
                    view = "game"
                    accumulator = 0.0
                elif view != "game" or settings_open:
                    continue
                elif event.key == pygame.K_r:
                    view = "modes"
                    pending_directions.clear()
                    accumulator = 0.0
                elif event.key in (pygame.K_SPACE, pygame.K_p):
                    state = toggle_pause(state)
                    settings_open = False
                    accumulator = 0.0
                elif event.key == pygame.K_s and state.status == "paused":
                    settings_open = True
                elif event.key in KEY_DIRECTIONS and state.status in ("ready", "running"):
                    requested = KEY_DIRECTIONS[event.key]
                    basis = pending_directions[-1] if pending_directions else state.direction
                    accepted = change_direction(basis, requested)
                    if accepted != requested:
                        continue
                    if state.status == "ready":
                        state = start_or_turn(state, accepted)
                        accumulator = 0.0
                    elif accepted != basis and len(pending_directions) < pending_directions.maxlen:
                        pending_directions.append(accepted)
                continue

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                editor_dragging = False
                last_editor_cell = None
                continue

            if event.type == pygame.MOUSEMOTION and view == "editor" and editor_dragging:
                if editor_ui is not None and event.buttons[0]:
                    cell = editor_cell_at(event.pos, editor_ui, editor)
                    if cell is not None and cell != last_editor_cell:
                        editor = set_editor_wall(editor, cell, editor_brush_add)
                        last_editor_cell = cell
                continue

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            if view == "editor" and editor_ui is not None:
                if editor_ui.back.collidepoint(event.pos):
                    editor = replace(editor, editing_name=False)
                    pygame.key.stop_text_input()
                    view = "maps"
                elif editor_ui.name.collidepoint(event.pos):
                    editor = replace(
                        editor,
                        editing_name=not editor.editing_name,
                        message="请输入地图名称" if not editor.editing_name else "名称编辑完成",
                    )
                    if editor.editing_name:
                        pygame.key.start_text_input()
                    else:
                        pygame.key.stop_text_input()
                elif editor_ui.clear.collidepoint(event.pos):
                    editor = clear_editor(editor)
                elif editor_ui.export.collidepoint(event.pos):
                    export_editor_map()
                elif editor_ui.play.collidepoint(event.pos):
                    play_editor_map()
                else:
                    cell = editor_cell_at(event.pos, editor_ui, editor)
                    if cell is not None:
                        editor_brush_add = cell not in editor.walls
                        editor = toggle_editor_wall(editor, cell)
                        editor_dragging = True
                        last_editor_cell = cell
                continue

            if view == "maps":
                visible = available_maps[map_page * 6 : map_page * 6 + 6]
                controls = map_library_controls(screen.get_size(), len(visible))
                selected_index = next(
                    (
                        index
                        for index, rect in enumerate(controls.cards)
                        if rect.collidepoint(event.pos)
                    ),
                    None,
                )
                if selected_index is not None:
                    launch_map(visible[selected_index])
                elif controls.back.collidepoint(event.pos):
                    view = "modes"
                elif controls.editor.collidepoint(event.pos):
                    editor = new_editor()
                    view = "editor"
                elif controls.refresh.collidepoint(event.pos):
                    refresh_maps()
                elif controls.previous.collidepoint(event.pos):
                    map_page = max(0, map_page - 1)
                elif controls.next.collidepoint(event.pos):
                    page_count = max(1, (len(available_maps) + 5) // 6)
                    map_page = min(page_count - 1, map_page + 1)
                continue

            if view == "modes":
                controls = mode_controls(screen.get_size())
                selected_mode: GameMode | None = None
                if controls.classic.collidepoint(event.pos):
                    selected_mode = "classic"
                elif controls.wrap.collidepoint(event.pos):
                    selected_mode = "wrap"
                elif controls.maze.collidepoint(event.pos):
                    selected_mode = "maze"
                elif controls.workshop.collidepoint(event.pos):
                    view = "maps"
                if selected_mode is not None:
                    state = new_game(mode=selected_mode)
                    view = "game"
                    accumulator = 0.0
                continue

            if settings_open:
                controls = settings_controls(screen.get_size())
                if controls.close.collidepoint(event.pos):
                    settings_open = False
                else:
                    for name, rect in controls.themes.items():
                        if rect.collidepoint(event.pos):
                            theme_name = name
                            break
                    for selected_language, rect in controls.languages.items():
                        if rect.collidepoint(event.pos):
                            language = selected_language
                            break
                    for selected_speed, rect in controls.speeds.items():
                        if rect.collidepoint(event.pos):
                            speed = selected_speed
                            break
                continue

            if layout is not None and layout.back.collidepoint(event.pos):
                running = False
            elif layout is not None and layout.restart.collidepoint(event.pos):
                view = "modes"
                pending_directions.clear()
                accumulator = 0.0
            elif layout is not None and layout.pause.collidepoint(event.pos):
                state = toggle_pause(state)
                accumulator = 0.0
            elif (
                layout is not None
                and layout.settings.collidepoint(event.pos)
                and state.status == "paused"
            ):
                settings_open = True

        if not running:
            continue

        if view == "game" and state.status == "running":
            state = elapse_bonus_timer(state, elapsed_ms)
            accumulator += simulation_elapsed_ms
            interval = move_interval_ms(speed)
            while accumulator >= interval and state.status == "running":
                accumulator -= interval
                if pending_directions:
                    state = start_or_turn(state, pending_directions.popleft())
                result = advance(state)
                state = result.state
                sounds.play_step(result)
                if state.score > best_score:
                    best_score = state.score
                    save_player_data(best_score, theme_name, language, speed=speed)
                interval = move_interval_ms(speed)
        else:
            accumulator = 0.0

    save_player_data(best_score, theme_name, language, speed=speed)
    return navigation
