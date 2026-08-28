"""Versioned Snake maps, built-in layouts, editor state, and JSON exchange."""

from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import GRID_HEIGHT, GRID_WIDTH, INITIAL_SNAKE_LENGTH

Cell = tuple[int, int]
MAP_FORMAT = "mini-game-collection.snake-map"
MAP_VERSION = 1
MIN_MAP_WIDTH = 8
MAX_MAP_WIDTH = 40
MIN_MAP_HEIGHT = 6
MAX_MAP_HEIGHT = 30
MIN_PLAYABLE_CELLS = 32


class MapFormatError(ValueError):
    """Raised when a map file is malformed or cannot produce a playable board."""


@dataclass(frozen=True)
class SnakeMap:
    name: str
    width: int
    height: int
    walls: frozenset[Cell]
    author: str = ""
    description: str = ""


@dataclass(frozen=True)
class EditorState:
    name: str
    width: int
    height: int
    walls: frozenset[Cell] = frozenset()
    message: str = "点击格子绘制墙体"
    editing_name: bool = False


def initial_snake_cells(width: int, height: int) -> tuple[Cell, ...]:
    head_x = width // 2
    head_y = height // 2
    return tuple((head_x - offset, head_y) for offset in range(INITIAL_SNAKE_LENGTH))


def protected_cells(width: int, height: int) -> frozenset[Cell]:
    """Cells reserved for the initial snake and its three legal first moves."""

    snake = initial_snake_cells(width, height)
    head_x, head_y = snake[0]
    exits = ((head_x + 1, head_y), (head_x, head_y - 1), (head_x, head_y + 1))
    return frozenset((*snake, *exits))


def _reachable_cells(width: int, height: int, walls: frozenset[Cell]) -> set[Cell]:
    free = {
        (column, row)
        for row in range(height)
        for column in range(width)
        if (column, row) not in walls
    }
    if not free:
        return set()
    start = initial_snake_cells(width, height)[0]
    if start not in free:
        return set()
    visited = {start}
    queue = deque((start,))
    while queue:
        column, row = queue.popleft()
        for neighbor in (
            (column + 1, row),
            (column - 1, row),
            (column, row + 1),
            (column, row - 1),
        ):
            if neighbor in free and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited


def validate_map(game_map: SnakeMap) -> SnakeMap:
    if not isinstance(game_map.name, str) or not game_map.name.strip():
        raise MapFormatError("地图名称不能为空")
    if len(game_map.name.strip()) > 48:
        raise MapFormatError("地图名称不能超过 48 个字符")
    if (
        isinstance(game_map.width, bool)
        or not isinstance(game_map.width, int)
        or not MIN_MAP_WIDTH <= game_map.width <= MAX_MAP_WIDTH
    ):
        raise MapFormatError(f"地图宽度必须在 {MIN_MAP_WIDTH} 到 {MAX_MAP_WIDTH} 之间")
    if (
        isinstance(game_map.height, bool)
        or not isinstance(game_map.height, int)
        or not MIN_MAP_HEIGHT <= game_map.height <= MAX_MAP_HEIGHT
    ):
        raise MapFormatError(f"地图高度必须在 {MIN_MAP_HEIGHT} 到 {MAX_MAP_HEIGHT} 之间")
    if any(
        isinstance(column, bool)
        or isinstance(row, bool)
        or not isinstance(column, int)
        or not isinstance(row, int)
        or not (0 <= column < game_map.width and 0 <= row < game_map.height)
        for column, row in game_map.walls
    ):
        raise MapFormatError("地图包含越界或无效的墙体坐标")
    if game_map.walls & protected_cells(game_map.width, game_map.height):
        raise MapFormatError("墙体不能占用贪吃蛇出生区")
    playable_count = game_map.width * game_map.height - len(game_map.walls)
    if playable_count < MIN_PLAYABLE_CELLS:
        raise MapFormatError(f"地图至少需要保留 {MIN_PLAYABLE_CELLS} 个可游玩格子")
    if len(_reachable_cells(game_map.width, game_map.height, game_map.walls)) != playable_count:
        raise MapFormatError("所有可游玩区域必须互相连通")
    return replace(
        game_map,
        name=game_map.name.strip(),
        author=game_map.author.strip()[:48],
        description=game_map.description.strip()[:160],
    )


def _classic_walls(width: int, height: int) -> frozenset[Cell]:
    walls: set[Cell] = set()

    def vertical(x: int, start: int, end: int, gaps: set[int]) -> None:
        walls.update((x, row) for row in range(start, end) if row not in gaps)

    def horizontal(row: int, start: int, end: int, gaps: set[int]) -> None:
        walls.update((column, row) for column in range(start, end) if column not in gaps)

    vertical(4, 1, 14, {4, 9})
    vertical(11, 1, 8, {5})
    vertical(18, 2, 16, {6, 12})
    vertical(8, 11, 17, {14})
    vertical(15, 10, 17, {13})
    horizontal(3, 5, 11, {8})
    horizontal(7, 6, 18, {10, 14})
    horizontal(10, 16, 23, {20})
    horizontal(12, 1, 8, {4})
    horizontal(15, 9, 21, {13, 17})
    return frozenset(walls - set(protected_cells(width, height)))


def _crossroads_walls(width: int, height: int) -> frozenset[Cell]:
    walls = {
        (width // 2, row)
        for row in range(2, height - 2)
        if row not in {height // 4, height // 2, height * 3 // 4}
    }
    walls.update(
        (column, height // 2)
        for column in range(2, width - 2)
        if column not in {width // 4, width // 2, width * 3 // 4}
    )
    return frozenset(walls - set(protected_cells(width, height)))


def _islands_walls(width: int, height: int) -> frozenset[Cell]:
    walls: set[Cell] = set()
    for center_x, center_y in ((5, 4), (18, 4), (5, 13), (18, 13), (12, 5), (12, 13)):
        for x in range(center_x - 1, center_x + 2):
            for y in range(center_y - 1, center_y + 2):
                walls.add((x, y))
    return frozenset(walls - set(protected_cells(width, height)))


def _gates_walls(width: int, height: int) -> frozenset[Cell]:
    walls: set[Cell] = set()
    for row in (4, 9, 14):
        gaps = {3 + (row * 2) % 7, width // 2, width - 5}
        walls.update((column, row) for column in range(1, width - 1) if column not in gaps)
    return frozenset(walls - set(protected_cells(width, height)))


BUILTIN_MAPS: tuple[SnakeMap, ...] = (
    SnakeMap(
        "经典迷宫",
        GRID_WIDTH,
        GRID_HEIGHT,
        _classic_walls(GRID_WIDTH, GRID_HEIGHT),
        description="宽通道与交错墙体",
    ),
    SnakeMap(
        "十字路口",
        GRID_WIDTH,
        GRID_HEIGHT,
        _crossroads_walls(GRID_WIDTH, GRID_HEIGHT),
        description="多入口中央十字",
    ),
    SnakeMap(
        "群岛",
        GRID_WIDTH,
        GRID_HEIGHT,
        _islands_walls(GRID_WIDTH, GRID_HEIGHT),
        description="六座方形障碍岛",
    ),
    SnakeMap(
        "闸门",
        GRID_WIDTH,
        GRID_HEIGHT,
        _gates_walls(GRID_WIDTH, GRID_HEIGHT),
        description="三道错位横向闸门",
    ),
)


def map_to_payload(game_map: SnakeMap) -> dict[str, Any]:
    game_map = validate_map(game_map)
    return {
        "format": MAP_FORMAT,
        "version": MAP_VERSION,
        "name": game_map.name,
        "width": game_map.width,
        "height": game_map.height,
        "walls": [
            list(cell) for cell in sorted(game_map.walls, key=lambda cell: (cell[1], cell[0]))
        ],
        "author": game_map.author,
        "description": game_map.description,
    }


def map_from_payload(payload: object) -> SnakeMap:
    if not isinstance(payload, dict):
        raise MapFormatError("地图文件顶层必须是 JSON 对象")
    if payload.get("format") != MAP_FORMAT or payload.get("version") != MAP_VERSION:
        raise MapFormatError("不支持的地图文件格式或版本")
    walls_value = payload.get("walls")
    if not isinstance(walls_value, list):
        raise MapFormatError("地图墙体必须是坐标列表")
    walls: set[Cell] = set()
    for value in walls_value:
        if not isinstance(value, list) or len(value) != 2:
            raise MapFormatError("每个墙体必须使用 [x, y] 坐标")
        column, row = value
        if (
            isinstance(column, bool)
            or isinstance(row, bool)
            or not isinstance(column, int)
            or not isinstance(row, int)
        ):
            raise MapFormatError("墙体坐标必须是整数")
        walls.add((column, row))
    name = payload.get("name")
    width = payload.get("width")
    height = payload.get("height")
    author = payload.get("author", "")
    description = payload.get("description", "")
    if not isinstance(name, str) or not isinstance(author, str) or not isinstance(description, str):
        raise MapFormatError("地图名称、作者和说明必须是文字")
    return validate_map(SnakeMap(name, width, height, frozenset(walls), author, description))


def load_map(path: Path) -> SnakeMap:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MapFormatError(f"无法读取地图文件：{error}") from error
    return map_from_payload(payload)


def save_map(game_map: SnakeMap, path: Path) -> Path:
    payload = map_to_payload(game_map)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as error:
        raise MapFormatError(f"无法保存地图文件：{error}") from error
    return path


def default_map_directory() -> Path:
    return Path.home() / "MiniGameCollection" / "snake_maps"


def _safe_stem(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-").lower()
    return stem[:40] or "snake-map"


def export_map(
    game_map: SnakeMap,
    directory: Path | None = None,
    filename: str | None = None,
) -> Path:
    directory = directory or default_map_directory()
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{_safe_stem(game_map.name)}-{timestamp}.snake-map.json"
    destination = directory / Path(filename).name
    base_stem = destination.stem
    suffix = destination.suffix or ".json"
    counter = 2
    while destination.exists():
        destination = directory / f"{base_stem}-{counter}{suffix}"
        counter += 1
    return save_map(game_map, destination)


def import_map_file(source: Path, directory: Path | None = None) -> tuple[SnakeMap, Path]:
    game_map = load_map(source)
    destination = export_map(game_map, directory, source.name)
    return game_map, destination


def discover_maps(directory: Path | None = None) -> tuple[tuple[SnakeMap, ...], tuple[str, ...]]:
    directory = directory or default_map_directory()
    if not directory.exists():
        return (), ()
    maps: list[SnakeMap] = []
    errors: list[str] = []
    try:
        paths = sorted(directory.glob("*.json"), key=lambda path: path.name.lower())
    except OSError as error:
        return (), (str(error),)
    for path in paths:
        try:
            maps.append(load_map(path))
        except MapFormatError as error:
            errors.append(f"{path.name}: {error}")
    return tuple(maps), tuple(errors)


def new_editor(width: int = GRID_WIDTH, height: int = GRID_HEIGHT) -> EditorState:
    return EditorState("我的地图", width, height)


def toggle_editor_wall(editor: EditorState, cell: Cell) -> EditorState:
    return set_editor_wall(editor, cell, cell not in editor.walls)


def set_editor_wall(editor: EditorState, cell: Cell, present: bool) -> EditorState:
    column, row = cell
    if not (0 <= column < editor.width and 0 <= row < editor.height):
        return replace(editor, message="格子位于地图范围之外")
    if cell in protected_cells(editor.width, editor.height):
        return replace(editor, message="绿色出生区不能放置墙体")
    walls = set(editor.walls)
    if present:
        walls.add(cell)
    else:
        walls.discard(cell)
    return replace(editor, walls=frozenset(walls), message=f"已绘制 {len(walls)} 个墙体")


def clear_editor(editor: EditorState) -> EditorState:
    return replace(editor, walls=frozenset(), message="地图已清空")


def editor_to_map(editor: EditorState) -> SnakeMap:
    return validate_map(SnakeMap(editor.name, editor.width, editor.height, editor.walls))
