"""Pure simulation rules for Pixel Aircraft Battle."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, replace
from typing import Literal

from .config import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    PLAYER_INVULNERABLE_MS,
    RAPID_FIRE_DURATION_MS,
)

GameStatus = Literal["ready", "running", "paused", "game_over"]
CraftKind = Literal["falcon", "viper", "guardian"]
EnemyKind = Literal["drone", "scout", "tank", "boss"]
PowerKind = Literal["rapid", "shield", "repair"]
ProjectileOwner = Literal["player", "enemy"]
ExplosionKind = Literal["enemy", "elite", "boss", "player"]


@dataclass(frozen=True)
class CraftSpec:
    name: str
    description: str
    speed: float
    fire_interval_ms: float
    max_lives: int
    bullet_damage: int
    bullet_count: int


CRAFT_SPECS: dict[CraftKind, CraftSpec] = {
    "falcon": CraftSpec("苍隼", "均衡 · 灵活可靠", 225.0, 175.0, 3, 1, 1),
    "viper": CraftSpec("蝰蛇", "高速 · 双联速射", 255.0, 145.0, 2, 1, 2),
    "guardian": CraftSpec("守卫", "重装 · 高伤耐久", 190.0, 225.0, 4, 2, 1),
}


@dataclass(frozen=True)
class Player:
    x: float
    y: float
    lives: int = 3
    invulnerable_ms: float = 0.0
    rapid_ms: float = 0.0
    shielded: bool = False
    craft: CraftKind = "falcon"


@dataclass(frozen=True)
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    owner: ProjectileOwner
    damage: int = 1


@dataclass(frozen=True)
class Enemy:
    id: int
    kind: EnemyKind
    x: float
    y: float
    vx: float
    vy: float
    hp: int
    shot_ms: float
    elite: bool = False
    max_hp: int = 0


@dataclass(frozen=True)
class PowerUp:
    kind: PowerKind
    x: float
    y: float
    vy: float = 58.0


@dataclass(frozen=True)
class Explosion:
    x: float
    y: float
    kind: ExplosionKind
    age_ms: float = 0.0
    duration_ms: float = 460.0


@dataclass(frozen=True)
class GameState:
    status: GameStatus
    player: Player
    projectiles: tuple[Projectile, ...] = ()
    enemies: tuple[Enemy, ...] = ()
    powerups: tuple[PowerUp, ...] = ()
    explosions: tuple[Explosion, ...] = ()
    score: int = 0
    kills: int = 0
    level: int = 1
    elapsed_ms: float = 0.0
    spawn_ms: float = 0.0
    fire_ms: float = 0.0
    next_id: int = 1
    next_boss_level: int = 5


@dataclass(frozen=True)
class Transition:
    state: GameState
    events: tuple[str, ...] = ()


def new_game(craft: CraftKind = "falcon") -> GameState:
    if craft not in CRAFT_SPECS:
        raise ValueError(f"Unknown aircraft: {craft}")
    spec = CRAFT_SPECS[craft]
    return GameState(
        status="ready",
        player=Player(ARENA_WIDTH / 2, ARENA_HEIGHT - 62, lives=spec.max_lives, craft=craft),
    )


def start(state: GameState) -> GameState:
    if state.status == "ready":
        return replace(state, status="running")
    return state


def toggle_pause(state: GameState) -> GameState:
    if state.status == "running":
        return replace(state, status="paused")
    if state.status == "paused":
        return replace(state, status="running")
    return state


def enemy_size(kind: EnemyKind) -> tuple[float, float]:
    if kind == "boss":
        return (82.0, 50.0)
    if kind == "tank":
        return (34.0, 30.0)
    if kind == "scout":
        return (24.0, 22.0)
    return (28.0, 24.0)


def _overlaps(
    ax: float,
    ay: float,
    aw: float,
    ah: float,
    bx: float,
    by: float,
    bw: float,
    bh: float,
) -> bool:
    return abs(ax - bx) * 2 < aw + bw and abs(ay - by) * 2 < ah + bh


def _spawn_enemy(state: GameState, rng: random.Random) -> Enemy:
    roll = rng.random()
    if state.level >= 3 and roll < min(0.12 + state.level * 0.015, 0.3):
        kind: EnemyKind = "tank"
        hp, speed, width = 4 + state.level // 5, 38.0 + state.level * 2, 34.0
        vx = 0.0
    elif roll < 0.52:
        kind = "scout"
        hp, speed, width = 1, 84.0 + state.level * 3, 24.0
        vx = rng.choice((-1.0, 1.0)) * (38.0 + state.level * 2)
    else:
        kind = "drone"
        hp, speed, width = 1, 57.0 + state.level * 2.5, 28.0
        vx = 0.0
    elite = state.level >= 2 and rng.random() < min(0.08 + state.level * 0.018, 0.28)
    if elite:
        hp = max(2, hp * 2)
        speed *= 1.16
    shot_ms = rng.uniform(850.0, 1900.0) * (0.68 if elite else 1.0)
    return Enemy(
        id=state.next_id,
        kind=kind,
        x=rng.uniform(width / 2 + 8, ARENA_WIDTH - width / 2 - 8),
        y=-24.0,
        vx=vx,
        vy=speed,
        hp=hp,
        shot_ms=shot_ms,
        elite=elite,
        max_hp=hp,
    )


def _spawn_boss(state: GameState) -> Enemy:
    hp = 30 + state.level * 4
    return Enemy(
        id=state.next_id,
        kind="boss",
        x=ARENA_WIDTH / 2,
        y=-45.0,
        vx=66.0 + state.level * 2,
        vy=38.0,
        hp=hp,
        shot_ms=1300.0,
        max_hp=hp,
    )


def _move_player(player: Player, movement: tuple[float, float], dt: float) -> Player:
    dx, dy = movement
    length = math.hypot(dx, dy)
    if length > 1.0:
        dx, dy = dx / length, dy / length
    speed = CRAFT_SPECS[player.craft].speed
    return replace(
        player,
        x=max(16.0, min(ARENA_WIDTH - 16.0, player.x + dx * speed * dt)),
        y=max(24.0, min(ARENA_HEIGHT - 22.0, player.y + dy * speed * dt)),
        invulnerable_ms=max(0.0, player.invulnerable_ms - dt * 1000),
        rapid_ms=max(0.0, player.rapid_ms - dt * 1000),
    )


def _damage_player(player: Player) -> tuple[Player, bool]:
    if player.invulnerable_ms > 0:
        return player, False
    if player.shielded:
        return replace(player, shielded=False, invulnerable_ms=400.0), True
    lives = max(0, player.lives - 1)
    return (
        replace(
            player,
            x=ARENA_WIDTH / 2,
            y=ARENA_HEIGHT - 62,
            lives=lives,
            invulnerable_ms=PLAYER_INVULNERABLE_MS if lives else 0.0,
        ),
        True,
    )


def _drop_powerup(enemy: Enemy, rng: random.Random) -> PowerUp | None:
    chance = 1.0 if enemy.kind == "boss" else 0.28 if enemy.elite else 0.14
    if rng.random() >= chance:
        return None
    roll = rng.random()
    kind: PowerKind = "rapid" if roll < 0.48 else "shield" if roll < 0.83 else "repair"
    return PowerUp(kind, enemy.x, enemy.y)


def _player_salvo(player: Player) -> tuple[tuple[Projectile, ...], float]:
    spec = CRAFT_SPECS[player.craft]
    rapid = player.rapid_ms > 0
    interval = spec.fire_interval_ms * (0.52 if rapid else 1.0)
    speed = -415.0 if rapid else -365.0
    count = 2 if rapid else spec.bullet_count
    offsets = (0.0,) if count == 1 else (-7.0, 7.0)
    return (
        tuple(
            Projectile(
                player.x + offset,
                player.y - 18,
                0,
                speed,
                "player",
                spec.bullet_damage,
            )
            for offset in offsets
        ),
        interval,
    )


def _enemy_salvo(enemy: Enemy, player: Player, level: int) -> tuple[Projectile, ...]:
    dx = player.x - enemy.x
    dy = max(50.0, player.y - enemy.y)
    base_angle = math.atan2(dy, dx)
    if enemy.kind == "boss":
        offsets = (-0.56, -0.28, 0.0, 0.28, 0.56)
        speed = 170.0 + level * 5
    elif enemy.elite:
        offsets = (-0.12, 0.12)
        speed = 168.0 + level * 6
    else:
        offsets = (0.0,)
        speed = 145.0 + level * 6
    return tuple(
        Projectile(
            enemy.x,
            enemy.y + enemy_size(enemy.kind)[1] / 2,
            math.cos(base_angle + offset) * speed,
            math.sin(base_angle + offset) * speed,
            "enemy",
        )
        for offset in offsets
    )


def advance(
    state: GameState,
    elapsed_ms: float,
    movement: tuple[float, float] = (0.0, 0.0),
    rng: random.Random | None = None,
) -> Transition:
    """Advance a running game by one bounded simulation step."""

    if state.status != "running":
        return Transition(state)
    rng = rng or random.Random()
    elapsed_ms = max(0.0, min(50.0, elapsed_ms))
    dt = elapsed_ms / 1000.0
    events: list[str] = []
    player = _move_player(state.player, movement, dt)
    explosions = [
        replace(explosion, age_ms=explosion.age_ms + elapsed_ms)
        for explosion in state.explosions
        if explosion.age_ms + elapsed_ms < explosion.duration_ms
    ]

    projectiles = [
        replace(
            projectile, x=projectile.x + projectile.vx * dt, y=projectile.y + projectile.vy * dt
        )
        for projectile in state.projectiles
    ]
    projectiles = [
        projectile
        for projectile in projectiles
        if -20 <= projectile.x <= ARENA_WIDTH + 20 and -30 <= projectile.y <= ARENA_HEIGHT + 30
    ]

    fire_ms = state.fire_ms - elapsed_ms
    if fire_ms <= 0:
        salvo, interval = _player_salvo(player)
        projectiles.extend(salvo)
        fire_ms += interval
        events.append("shot")

    enemies: list[Enemy] = []
    for enemy in state.enemies:
        x = enemy.x + enemy.vx * dt
        y = enemy.y + enemy.vy * dt
        width, _ = enemy_size(enemy.kind)
        vx = enemy.vx
        if x < width / 2 or x > ARENA_WIDTH - width / 2:
            x = max(width / 2, min(ARENA_WIDTH - width / 2, x))
            vx *= -1
        vy = enemy.vy
        if enemy.kind == "boss" and y >= 92.0:
            y = 92.0
            vy = 0.0
        shot_ms = enemy.shot_ms - elapsed_ms
        if shot_ms <= 0 and 0 < enemy.y < ARENA_HEIGHT * 0.68:
            firing_enemy = replace(enemy, x=x, y=y)
            projectiles.extend(_enemy_salvo(firing_enemy, player, state.level))
            if enemy.kind == "boss":
                shot_ms = 780.0
            else:
                shot_ms = rng.uniform(1200.0, 2300.0) / min(
                    2.0 if enemy.elite else 1.7,
                    (1.32 if enemy.elite else 1.0) + state.level * 0.04,
                )
            events.append("enemy_shot")
        enemies.append(replace(enemy, x=x, y=y, vx=vx, vy=vy, shot_ms=shot_ms))

    spawn_ms = state.spawn_ms + elapsed_ms
    interval = max(330.0, 900.0 - (state.level - 1) * 55.0)
    next_id = state.next_id
    next_boss_level = state.next_boss_level
    boss_active = any(enemy.kind == "boss" for enemy in enemies)
    if state.level >= next_boss_level and not boss_active:
        enemies.append(_spawn_boss(replace(state, next_id=next_id)))
        next_id += 1
        next_boss_level += 5
        spawn_ms = 0.0
        events.append("boss_warning")
    elif spawn_ms >= interval and not boss_active:
        spawn_ms -= interval
        spawned = _spawn_enemy(replace(state, next_id=next_id), rng)
        enemies.append(spawned)
        next_id += 1

    # Player projectiles damage only the first enemy they touch.
    kept_projectiles: list[Projectile] = []
    destroyed: list[Enemy] = []
    for projectile in projectiles:
        if projectile.owner != "player":
            kept_projectiles.append(projectile)
            continue
        hit_index = next(
            (
                index
                for index, enemy in enumerate(enemies)
                if _overlaps(
                    projectile.x,
                    projectile.y,
                    5,
                    12,
                    enemy.x,
                    enemy.y,
                    *enemy_size(enemy.kind),
                )
            ),
            None,
        )
        if hit_index is None:
            kept_projectiles.append(projectile)
            continue
        hit = enemies[hit_index]
        events.append("hit")
        if hit.hp <= projectile.damage:
            destroyed.append(hit)
            enemies.pop(hit_index)
        else:
            enemies[hit_index] = replace(hit, hp=hit.hp - projectile.damage)

    score = state.score
    kills = state.kills
    powerups = [replace(item, y=item.y + item.vy * dt) for item in state.powerups]
    for enemy in destroyed:
        points = {"drone": 100, "scout": 150, "tank": 350, "boss": 3000}[enemy.kind]
        score += points * (2 if enemy.elite else 1)
        kills += 1
        events.append("destroyed")
        if enemy.kind == "boss":
            events.append("boss_defeated")
            explosions.append(Explosion(enemy.x, enemy.y, "boss", duration_ms=1300.0))
        elif enemy.elite:
            events.append("elite_destroyed")
            explosions.append(Explosion(enemy.x, enemy.y, "elite", duration_ms=680.0))
        else:
            explosions.append(Explosion(enemy.x, enemy.y, "enemy"))
        drop = _drop_powerup(enemy, rng)
        if drop is not None:
            powerups.append(drop)

    # Enemy fire, body collisions, and escapes all use one invulnerability gate.
    survivors: list[Projectile] = []
    for projectile in kept_projectiles:
        if projectile.owner == "enemy" and _overlaps(
            projectile.x, projectile.y, 7, 9, player.x, player.y, 23, 27
        ):
            had_shield = player.shielded
            impact = (player.x, player.y)
            player, damaged = _damage_player(player)
            if damaged:
                events.append("shield" if had_shield else "hurt")
                if not had_shield:
                    explosions.append(Explosion(*impact, "player", duration_ms=620.0))
            continue
        survivors.append(projectile)

    kept_enemies: list[Enemy] = []
    for enemy in enemies:
        width, height = enemy_size(enemy.kind)
        collided = _overlaps(enemy.x, enemy.y, width, height, player.x, player.y, 23, 27)
        escaped = enemy.y - height / 2 > ARENA_HEIGHT
        if collided or escaped:
            had_shield = player.shielded
            impact = (player.x, player.y)
            player, damaged = _damage_player(player)
            if damaged:
                events.append("shield" if had_shield else "hurt")
                if not had_shield:
                    explosions.append(Explosion(*impact, "player", duration_ms=620.0))
            continue
        kept_enemies.append(enemy)

    kept_powerups: list[PowerUp] = []
    for item in powerups:
        if player.lives > 0 and _overlaps(item.x, item.y, 18, 18, player.x, player.y, 23, 27):
            if item.kind == "rapid":
                player = replace(player, rapid_ms=RAPID_FIRE_DURATION_MS)
            elif item.kind == "shield":
                player = replace(player, shielded=True)
            else:
                maximum_lives = CRAFT_SPECS[player.craft].max_lives
                player = replace(player, lives=min(maximum_lives, player.lives + 1))
            events.append("powerup")
        elif item.y < ARENA_HEIGHT + 20:
            kept_powerups.append(item)

    level = 1 + kills // 10
    status: GameStatus = "game_over" if player.lives <= 0 else "running"
    if status == "game_over":
        events.append("game_over")
    return Transition(
        GameState(
            status=status,
            player=player,
            projectiles=tuple(survivors),
            enemies=tuple(kept_enemies),
            powerups=tuple(kept_powerups),
            explosions=tuple(explosions),
            score=score,
            kills=kills,
            level=level,
            elapsed_ms=state.elapsed_ms + elapsed_ms,
            spawn_ms=spawn_ms,
            fire_ms=fire_ms,
            next_id=next_id,
            next_boss_level=next_boss_level,
        ),
        tuple(events),
    )
