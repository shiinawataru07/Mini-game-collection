"""Responsive pixel-art renderer for Pixel Aircraft Battle."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from games.common.controls import draw_button, draw_panel
from games.common.fonts import get_font

from .config import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    BACKGROUND,
    CYAN,
    GREEN,
    GRID,
    MUTED,
    PANEL,
    PANEL_LIGHT,
    PURPLE,
    RED,
    TEXT,
    YELLOW,
)
from .logic import CRAFT_SPECS, CraftKind, EnemyKind, GameState, PowerKind, enemy_size


@dataclass(frozen=True)
class Layout:
    arena: pygame.Rect
    stats: pygame.Rect
    back: pygame.Rect
    pause: pygame.Rect
    restart: pygame.Rect
    scale: float


@dataclass(frozen=True)
class CraftControls:
    modal: pygame.Rect
    cards: dict[CraftKind, pygame.Rect]


def page_layout(window_size: tuple[int, int]) -> Layout:
    width, height = window_size
    margin = max(12, min(22, width // 34))
    gap = max(10, min(18, width // 48))
    header = 76
    footer = 30
    stats_width = max(138, min(190, width // 4))
    available_width = width - margin * 2 - gap - stats_width
    available_height = height - header - footer
    scale = max(0.68, min(available_width / ARENA_WIDTH, available_height / ARENA_HEIGHT))
    arena = pygame.Rect(0, 0, round(ARENA_WIDTH * scale), round(ARENA_HEIGHT * scale))
    group_width = arena.width + gap + stats_width
    arena.left = (width - group_width) // 2
    arena.top = header + max(0, (available_height - arena.height) // 2)
    stats = pygame.Rect(arena.right + gap, arena.top, stats_width, arena.height)
    button_width = max(72, min(92, (width - margin * 2 - 16) // 3))
    back = pygame.Rect(margin, 20, button_width, 36)
    pause = pygame.Rect(back.right + 8, 20, button_width, 36)
    restart = pygame.Rect(width - margin - button_width, 20, button_width, 36)
    return Layout(arena, stats, back, pause, restart, scale)


def craft_controls(window_size: tuple[int, int]) -> CraftControls:
    width, height = window_size
    modal = pygame.Rect(0, 0, min(700, width - 30), min(390, height - 100))
    modal.center = (width // 2, height // 2 + 18)
    gap = 12
    padding = 22
    card_width = (modal.width - padding * 2 - gap * 2) // 3
    cards: dict[CraftKind, pygame.Rect] = {
        craft: pygame.Rect(
            modal.left + padding + index * (card_width + gap),
            modal.top + 86,
            card_width,
            modal.height - 118,
        )
        for index, craft in enumerate(CRAFT_SPECS)
    }
    return CraftControls(modal, cards)


def _pixel_rect(layout: Layout, x: float, y: float, w: float, h: float) -> pygame.Rect:
    return pygame.Rect(
        round(layout.arena.left + (x - w / 2) * layout.scale),
        round(layout.arena.top + (y - h / 2) * layout.scale),
        max(1, round(w * layout.scale)),
        max(1, round(h * layout.scale)),
    )


def _draw_sprite(
    screen: pygame.Surface,
    layout: Layout,
    x: float,
    y: float,
    pattern: tuple[str, ...],
    palette: dict[str, tuple[int, int, int]],
    pixel: int = 3,
) -> None:
    cell = max(2, round(pixel * layout.scale))
    center = (
        round(layout.arena.left + x * layout.scale),
        round(layout.arena.top + y * layout.scale),
    )
    _draw_pattern(screen, pattern, center, cell, palette)


def _draw_pattern(
    screen: pygame.Surface,
    pattern: tuple[str, ...],
    center: tuple[int, int],
    cell: int,
    palette: dict[str, tuple[int, int, int]],
) -> None:
    width = len(pattern[0]) * cell
    height = len(pattern) * cell
    left = center[0] - width // 2
    top = center[1] - height // 2
    for row, line in enumerate(pattern):
        for column, symbol in enumerate(line):
            color = palette.get(symbol)
            if color is not None:
                pygame.draw.rect(
                    screen,
                    color,
                    (left + column * cell, top + row * cell, cell, cell),
                )


FALCON_PATTERN = (
    "....C....",
    "...CCC...",
    "...WWW...",
    "..CWCWC..",
    ".CCWCWCC.",
    "CCCWCWCCC",
    "..CCCCC..",
    "...Y.Y...",
    "...Y.Y...",
)
VIPER_PATTERN = (
    "...P...",
    "..PPP..",
    ".PPWPP.",
    "PPWWWPP",
    ".PPWPP.",
    "..PPP..",
    ".PP.PP.",
    "PP...PP",
    "Y.....Y",
)
GUARDIAN_PATTERN = (
    ".....G.....",
    "....GGG....",
    "...GGWGG...",
    "..GGWWWGG..",
    ".GGGWGWGGG.",
    "GGGGWGWGGGG",
    "GG.GGGGG.GG",
    "...GGGGG...",
    "..Y.....Y..",
)
DRONE_PATTERN = (
    "RR.....RR",
    ".RR...RR.",
    "..RRRRR..",
    ".RRWRWRR.",
    "RRRRRRRRR",
    "..R.R.R..",
    ".R.....R.",
)
SCOUT_PATTERN = (
    "...P...",
    "..PPP..",
    ".PPWPP.",
    "PPPPPPP",
    "P.PPP.P",
    "..P.P..",
)
TANK_PATTERN = (
    "..YYYYY..",
    ".YYYYYYY.",
    "YYYWYWYYY",
    "YYYYYYYYY",
    "Y.YYYYY.Y",
    "..YY.YY..",
    ".YY...YY.",
    "YY.....YY",
)
BOSS_PATTERN = (
    ".R.................R.",
    ".RRR.............RRR.",
    "..RRR...RRRRR...RRR..",
    "...RRRRRRRRRRRRRRR...",
    "....RRRWWRRRWWRRR....",
    "..RRRRRRRRRRRRRRRRR..",
    ".RRRRR.RRRRRRR.RRRRR.",
    "RRR...RRRRRRRRR...RRR",
    ".R....RRR...RRR....R.",
    ".....RR.......RR.....",
    "....YY.........YY....",
)

PLAYER_PATTERNS: dict[CraftKind, tuple[str, ...]] = {
    "falcon": FALCON_PATTERN,
    "viper": VIPER_PATTERN,
    "guardian": GUARDIAN_PATTERN,
}
PLAYER_PALETTES: dict[CraftKind, dict[str, tuple[int, int, int]]] = {
    "falcon": {"C": CYAN, "W": TEXT, "Y": YELLOW},
    "viper": {"P": PURPLE, "W": TEXT, "Y": YELLOW},
    "guardian": {"G": GREEN, "W": TEXT, "Y": YELLOW},
}


def _draw_arena_background(screen: pygame.Surface, state: GameState, layout: Layout) -> None:
    pygame.draw.rect(screen, BACKGROUND, layout.arena)
    cell = max(3, round(12 * layout.scale))
    for x in range(layout.arena.left, layout.arena.right, cell):
        pygame.draw.line(screen, (12, 22, 43), (x, layout.arena.top), (x, layout.arena.bottom))
    for y in range(layout.arena.top, layout.arena.bottom, cell):
        pygame.draw.line(screen, (12, 22, 43), (layout.arena.left, y), (layout.arena.right, y))

    scroll = state.elapsed_ms * 0.025
    for index in range(36):
        x = (index * 79 + index * index * 11) % ARENA_WIDTH
        y = (index * 137 + scroll * (1 + index % 3)) % ARENA_HEIGHT
        size = 1.2 if index % 5 else 2.2
        color = (76, 111, 157) if index % 4 else (139, 178, 215)
        pygame.draw.rect(screen, color, _pixel_rect(layout, x, y, size, size))


def _draw_entities(screen: pygame.Surface, state: GameState, layout: Layout) -> None:
    for projectile in state.projectiles:
        color = CYAN if projectile.owner == "player" else RED
        height = 10 if projectile.owner == "player" else 7
        pygame.draw.rect(screen, color, _pixel_rect(layout, projectile.x, projectile.y, 3, height))
        if projectile.owner == "player":
            glow = _pixel_rect(layout, projectile.x, projectile.y + 5, 1.5, 4)
            pygame.draw.rect(screen, (185, 255, 248), glow)

    for item in state.powerups:
        colors: dict[PowerKind, tuple[int, int, int]] = {
            "rapid": YELLOW,
            "shield": CYAN,
            "repair": GREEN,
        }
        rect = _pixel_rect(layout, item.x, item.y, 17, 17)
        pygame.draw.rect(screen, colors[item.kind], rect)
        pygame.draw.rect(screen, TEXT, rect, width=max(1, round(layout.scale * 2)))
        label = {"rapid": "R", "shield": "S", "repair": "+"}[item.kind]
        font = get_font(max(10, round(11 * layout.scale)), bold=True)
        glyph = font.render(label, False, BACKGROUND)
        screen.blit(glyph, glyph.get_rect(center=rect.center))

    patterns: dict[EnemyKind, tuple[str, ...]] = {
        "drone": DRONE_PATTERN,
        "scout": SCOUT_PATTERN,
        "tank": TANK_PATTERN,
        "boss": BOSS_PATTERN,
    }
    palette = {"R": RED, "P": PURPLE, "Y": YELLOW, "W": TEXT}
    for enemy in state.enemies:
        pixel = 3 if enemy.kind != "boss" else 3
        enemy_palette = dict(palette)
        if enemy.elite:
            enemy_palette.update({"R": (255, 139, 78), "P": (218, 118, 255), "Y": TEXT})
        _draw_sprite(
            screen,
            layout,
            enemy.x,
            enemy.y,
            patterns[enemy.kind],
            enemy_palette,
            pixel,
        )
        if enemy.elite:
            width, height = enemy_size(enemy.kind)
            marker = _pixel_rect(layout, enemy.x, enemy.y, width + 8, height + 8)
            edge = max(2, round(5 * layout.scale))
            color = (255, 176, 84)
            for point in (
                (marker.left, marker.top, edge, 2),
                (marker.left, marker.top, 2, edge),
                (marker.right - edge, marker.top, edge, 2),
                (marker.right - 2, marker.top, 2, edge),
                (marker.left, marker.bottom - 2, edge, 2),
                (marker.left, marker.bottom - edge, 2, edge),
                (marker.right - edge, marker.bottom - 2, edge, 2),
                (marker.right - 2, marker.bottom - edge, 2, edge),
            ):
                pygame.draw.rect(screen, color, point)
            badge = get_font(max(8, round(9 * layout.scale)), bold=True).render(
                "ELITE", False, color
            )
            screen.blit(badge, badge.get_rect(midbottom=(marker.centerx, marker.top - 2)))
        if enemy.kind == "tank" and enemy.hp > 1:
            width, _ = enemy_size(enemy.kind)
            bar = _pixel_rect(layout, enemy.x, enemy.y - 21, width, 3)
            pygame.draw.rect(screen, (55, 36, 48), bar)
            maximum_hp = enemy.max_hp or enemy.hp
            hp_width = max(1, round(bar.width * min(1.0, enemy.hp / maximum_hp)))
            pygame.draw.rect(screen, YELLOW, (bar.left, bar.top, hp_width, bar.height))

    boss = next((enemy for enemy in state.enemies if enemy.kind == "boss"), None)
    if boss is not None:
        bar = pygame.Rect(
            layout.arena.left + round(28 * layout.scale),
            layout.arena.top + round(14 * layout.scale),
            layout.arena.width - round(56 * layout.scale),
            max(6, round(8 * layout.scale)),
        )
        pygame.draw.rect(screen, (49, 20, 39), bar)
        fill = round(bar.width * boss.hp / max(1, boss.max_hp))
        pygame.draw.rect(screen, RED, (bar.left, bar.top, fill, bar.height))
        pygame.draw.rect(screen, TEXT, bar, width=max(1, round(layout.scale)))
        label = get_font(max(10, round(11 * layout.scale)), "zh", bold=True).render(
            "BOSS", False, TEXT
        )
        screen.blit(label, label.get_rect(midbottom=(bar.centerx, bar.top - 2)))

    blink = state.player.invulnerable_ms > 0 and int(state.player.invulnerable_ms / 90) % 2 == 0
    if not blink:
        _draw_sprite(
            screen,
            layout,
            state.player.x,
            state.player.y,
            PLAYER_PATTERNS[state.player.craft],
            PLAYER_PALETTES[state.player.craft],
        )
    if state.player.shielded:
        pygame.draw.rect(
            screen,
            CYAN,
            _pixel_rect(layout, state.player.x, state.player.y, 37, 39),
            width=max(1, round(2 * layout.scale)),
        )

    _draw_explosions(screen, state, layout)


def _draw_explosions(screen: pygame.Surface, state: GameState, layout: Layout) -> None:
    colors = {
        "enemy": (YELLOW, RED, TEXT),
        "elite": (TEXT, (255, 156, 65), PURPLE),
        "boss": (TEXT, RED, YELLOW),
        "player": (CYAN, TEXT, RED),
    }
    counts = {"enemy": 10, "elite": 16, "boss": 30, "player": 18}
    sizes = {"enemy": 22.0, "elite": 32.0, "boss": 68.0, "player": 34.0}
    for explosion in state.explosions:
        progress = min(1.0, explosion.age_ms / explosion.duration_ms)
        count = counts[explosion.kind]
        radius = sizes[explosion.kind] * (0.2 + progress)
        palette = colors[explosion.kind]
        for index in range(count):
            angle = index * 2.39996 + (index % 3) * 0.17
            distance = radius * (0.45 + (index * 37 % 53) / 100)
            x = explosion.x + pygame.math.Vector2(1, 0).rotate_rad(angle).x * distance
            y = explosion.y + pygame.math.Vector2(1, 0).rotate_rad(angle).y * distance
            pixel = max(1.5, (4.5 - progress * 3) * (1.5 if explosion.kind == "boss" else 1))
            pygame.draw.rect(
                screen,
                palette[index % len(palette)],
                _pixel_rect(layout, x, y, pixel, pixel),
            )


def _stat(screen: pygame.Surface, rect: pygame.Rect, y: int, label: str, value: str) -> int:
    label_surface = get_font(13, "zh").render(label, True, MUTED)
    value_surface = get_font(24, "zh", bold=True).render(value, False, TEXT)
    screen.blit(label_surface, (rect.left + 16, y))
    screen.blit(value_surface, (rect.left + 16, y + 19))
    return y + 62


def _draw_stats(screen: pygame.Surface, state: GameState, best_score: int, layout: Layout) -> None:
    draw_panel(screen, layout.stats, PANEL, border_color=GRID, border_radius=4)
    craft = CRAFT_SPECS[state.player.craft]
    title = get_font(17, "zh", bold=True).render(f"{craft.name} · 状态", False, CYAN)
    screen.blit(title, (layout.stats.left + 16, layout.stats.top + 16))
    pygame.draw.rect(
        screen,
        CYAN,
        (layout.stats.left + 16, layout.stats.top + 45, layout.stats.width - 32, 3),
    )
    y = layout.stats.top + 64
    y = _stat(screen, layout.stats, y, "得分  SCORE", f"{state.score:06d}")
    y = _stat(screen, layout.stats, y, "最高  BEST", f"{best_score:06d}")
    y = _stat(screen, layout.stats, y, "波次  LEVEL", f"{state.level:02d}")
    y = _stat(screen, layout.stats, y, "击破  KILLS", f"{state.kills:03d}")

    lives_label = get_font(13, "zh").render("生命  LIVES", True, MUTED)
    screen.blit(lives_label, (layout.stats.left + 16, y))
    for index in range(craft.max_lives):
        color = RED if index < state.player.lives else (63, 55, 72)
        heart = pygame.Rect(layout.stats.left + 16 + index * 31, y + 27, 22, 16)
        pygame.draw.rect(screen, color, (heart.left, heart.top, 8, 8))
        pygame.draw.rect(screen, color, (heart.left + 12, heart.top, 8, 8))
        pygame.draw.rect(screen, color, (heart.left + 4, heart.top + 4, 16, 8))
        pygame.draw.rect(screen, color, (heart.left + 8, heart.top + 12, 8, 4))

    ability_y = layout.stats.bottom - 124
    if state.player.rapid_ms > 0:
        label = f"RAPID {state.player.rapid_ms / 1000:.1f}s"
        color = YELLOW
    elif state.player.shielded:
        label = "SHIELD READY"
        color = CYAN
    else:
        label = "AUTO FIRE"
        color = GREEN
    box = pygame.Rect(layout.stats.left + 12, ability_y, layout.stats.width - 24, 36)
    pygame.draw.rect(screen, PANEL_LIGHT, box)
    pygame.draw.rect(screen, color, box, width=2)
    status = get_font(12, bold=True).render(label, False, color)
    screen.blit(status, status.get_rect(center=box.center))

    hint_lines = ("方向键 / WASD 移动", "P 暂停 · R 重开", "C 选择战机", "Esc 返回菜单")
    for index, line in enumerate(hint_lines):
        hint = get_font(11, "zh").render(line, True, MUTED)
        screen.blit(
            hint,
            hint.get_rect(center=(layout.stats.centerx, layout.stats.bottom - 68 + index * 15)),
        )


def _draw_overlay(screen: pygame.Surface, state: GameState, layout: Layout) -> None:
    if state.status == "running":
        return
    shade = pygame.Surface(layout.arena.size, pygame.SRCALPHA)
    shade.fill((5, 9, 23, 195))
    screen.blit(shade, layout.arena.topleft)
    if state.status == "ready":
        title, subtitle, color = "像素空战", "按方向键 / WASD / 空格起飞", CYAN
    elif state.status == "paused":
        title, subtitle, color = "暂停", "按 P 或点击继续", YELLOW
    else:
        title, subtitle, color = "任务失败", "按 R / 空格重新出击", RED
    title_surface = get_font(max(27, round(34 * layout.scale)), "zh", bold=True).render(
        title, False, color
    )
    subtitle_surface = get_font(max(13, round(15 * layout.scale)), "zh").render(
        subtitle, True, TEXT
    )
    center_y = layout.arena.centery - 22
    screen.blit(title_surface, title_surface.get_rect(center=(layout.arena.centerx, center_y)))
    screen.blit(
        subtitle_surface,
        subtitle_surface.get_rect(center=(layout.arena.centerx, center_y + 48)),
    )


def _draw_craft_selection(screen: pygame.Surface, selected: CraftKind) -> None:
    controls = craft_controls(screen.get_size())
    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((4, 8, 20, 225))
    screen.blit(shade, (0, 0))
    draw_panel(screen, controls.modal, PANEL, border_color=CYAN, border_radius=6)
    title = get_font(25, "zh", bold=True).render("选择出击战机", False, TEXT)
    subtitle = get_font(13, "zh").render("按 1 / 2 / 3 或点击战机", True, MUTED)
    screen.blit(title, title.get_rect(center=(controls.modal.centerx, controls.modal.top + 34)))
    screen.blit(
        subtitle,
        subtitle.get_rect(center=(controls.modal.centerx, controls.modal.top + 64)),
    )
    colors: dict[CraftKind, tuple[int, int, int]] = {
        "falcon": CYAN,
        "viper": PURPLE,
        "guardian": GREEN,
    }
    for index, (craft, rect) in enumerate(controls.cards.items(), start=1):
        spec = CRAFT_SPECS[craft]
        color = colors[craft]
        pygame.draw.rect(screen, PANEL_LIGHT, rect)
        pygame.draw.rect(screen, color if craft == selected else GRID, rect, width=3)
        badge = get_font(14, bold=True).render(str(index), False, color)
        screen.blit(badge, (rect.left + 10, rect.top + 8))
        _draw_pattern(
            screen,
            PLAYER_PATTERNS[craft],
            (rect.centerx, rect.top + 69),
            max(2, min(4, rect.width // 38)),
            PLAYER_PALETTES[craft],
        )
        name = get_font(18, "zh", bold=True).render(spec.name, False, color)
        description = get_font(12, "zh").render(spec.description, True, TEXT)
        screen.blit(name, name.get_rect(center=(rect.centerx, rect.top + 122)))
        screen.blit(description, description.get_rect(center=(rect.centerx, rect.top + 149)))
        stats = (
            f"速度  {round(spec.speed)}",
            f"火力  {spec.bullet_damage} × {spec.bullet_count}",
            f"生命  {spec.max_lives}",
        )
        for row, line in enumerate(stats):
            label = get_font(11, "zh").render(line, True, MUTED)
            screen.blit(label, label.get_rect(center=(rect.centerx, rect.top + 180 + row * 20)))


def draw_game(
    screen: pygame.Surface,
    state: GameState,
    best_score: int,
    selecting_craft: bool = False,
) -> Layout:

    layout = page_layout(screen.get_size())
    screen.fill((11, 17, 34))
    draw_button(screen, layout.back, "返回", PANEL, TEXT, 15, "zh", border_color=GRID)
    pause_label = "继续" if state.status == "paused" else "暂停"
    draw_button(screen, layout.pause, pause_label, PANEL, TEXT, 15, "zh", border_color=GRID)
    draw_button(screen, layout.restart, "重新出击", PANEL, TEXT, 15, "zh", border_color=GRID)
    header = get_font(20, "zh", bold=True).render("PIXEL STRIKER", False, CYAN)
    screen.blit(header, header.get_rect(center=(screen.get_width() // 2, 38)))
    _draw_arena_background(screen, state, layout)
    _draw_entities(screen, state, layout)
    pygame.draw.rect(screen, CYAN, layout.arena, width=max(2, round(layout.scale * 2)))
    _draw_stats(screen, state, best_score, layout)
    _draw_overlay(screen, state, layout)
    if selecting_craft:
        _draw_craft_selection(screen, state.player.craft)
    return layout
