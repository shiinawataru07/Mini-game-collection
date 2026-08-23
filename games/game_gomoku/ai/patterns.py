"""Exact local threat classification for move ordering and evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from ..config import BOARD_SIZE
from ..logic import DIRECTIONS, Position
from .position import SearchPosition

WIN_SCORE = 800_000


class ThreatKind(IntEnum):
    NONE = 0
    OPEN_TWO = 1
    CLOSED_THREE = 2
    OPEN_THREE = 3
    DOUBLE_THREE = 4
    FOUR = 5
    FOUR_THREE = 6
    OPEN_FOUR = 7
    DOUBLE_FOUR = 8
    FIVE = 9


@dataclass(frozen=True)
class ThreatProfile:
    kind: ThreatKind
    four_directions: int = 0
    open_three_directions: int = 0
    closed_three_directions: int = 0
    open_two_directions: int = 0
    winning_points: tuple[Position, ...] = ()


_ORDERING_PATTERNS: tuple[tuple[int, tuple[str, ...]], ...] = (
    (220_000, (".XXXX.",)),
    (38_000, ("XXXX.", ".XXXX", "XXX.X", "XX.XX", "X.XXX")),
    (10_000, (".XXX.", ".XX.X.", ".X.XX.")),
    (1_800, ("XXX..", "..XXX", "XX.X.", ".X.XX", "X.XX.", ".XX..X.")),
    (450, (".XX.", ".X.X.", ".X..X.")),
    (60, (".X.",)),
)


def _inside(row: int, column: int) -> bool:
    return 0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE


def _line_cells(
    anchor: Position,
    delta_row: int,
    delta_column: int,
    radius: int = 4,
) -> list[Position]:
    row, column = anchor
    return [
        (row + offset * delta_row, column + offset * delta_column)
        for offset in range(-radius, radius + 1)
        if _inside(row + offset * delta_row, column + offset * delta_column)
    ]


def _winning_segment_contains(
    position: SearchPosition,
    move: Position,
    anchor: Position,
    player: int,
    delta_row: int,
    delta_column: int,
) -> bool:
    row, column = move
    segment: list[Position] = [move]
    for sign in (-1, 1):
        step = 1
        while True:
            candidate = (
                row + delta_row * step * sign,
                column + delta_column * step * sign,
            )
            if not _inside(*candidate) or position.board[candidate[0]][candidate[1]] != player:
                break
            if sign < 0:
                segment.insert(0, candidate)
            else:
                segment.append(candidate)
            step += 1
    return len(segment) >= 5 and anchor in segment


def _winning_points_in_direction(
    position: SearchPosition,
    anchor: Position,
    player: int,
    delta_row: int,
    delta_column: int,
) -> tuple[Position, ...]:
    wins: list[Position] = []
    for candidate in _line_cells(anchor, delta_row, delta_column):
        row, column = candidate
        if position.board[row][column] != 0:
            continue
        position.board[row][column] = player
        try:
            if _winning_segment_contains(
                position,
                candidate,
                anchor,
                player,
                delta_row,
                delta_column,
            ):
                wins.append(candidate)
        finally:
            position.board[row][column] = 0
    return tuple(wins)


def _extension_counts(
    position: SearchPosition,
    anchor: Position,
    player: int,
    delta_row: int,
    delta_column: int,
) -> tuple[int, int]:
    """Return counts of extensions that produce open and closed fours."""

    open_extensions = 0
    closed_extensions = 0
    for extension in _line_cells(anchor, delta_row, delta_column):
        row, column = extension
        if extension == anchor or position.board[row][column] != 0:
            continue
        position.board[row][column] = player
        try:
            wins = _winning_points_in_direction(
                position,
                anchor,
                player,
                delta_row,
                delta_column,
            )
        finally:
            position.board[row][column] = 0
        if len(wins) >= 2:
            open_extensions += 1
        elif len(wins) == 1:
            closed_extensions += 1
    return open_extensions, closed_extensions


def _direction_text(
    position: SearchPosition,
    anchor: Position,
    player: int,
    delta_row: int,
    delta_column: int,
) -> str:
    cells = []
    for row, column in _line_cells(anchor, delta_row, delta_column):
        stone = position.board[row][column]
        cells.append("X" if stone == player else "." if stone == 0 else "#")
    return "".join(cells)


def _ordering_line(
    position: SearchPosition,
    move: Position,
    player: int,
    delta_row: int,
    delta_column: int,
) -> str:
    cells = []
    move_row, move_column = move
    for offset in range(-5, 6):
        row = move_row + delta_row * offset
        column = move_column + delta_column * offset
        if not _inside(row, column):
            cells.append("#")
            continue
        stone = player if offset == 0 else position.board[row][column]
        cells.append("X" if stone == player else "." if stone == 0 else "#")
    return "".join(cells)


def _pattern_through_anchor(line: str, pattern: str) -> bool:
    start = line.find(pattern)
    while start >= 0:
        anchor_offset = 5 - start
        if 0 <= anchor_offset < len(pattern) and pattern[anchor_offset] == "X":
            return True
        start = line.find(pattern, start + 1)
    return False


def analyze_move(position: SearchPosition, move: Position, player: int) -> ThreatProfile:
    """Classify threats genuinely created by a virtual move."""

    if not position.is_legal(move):
        return ThreatProfile(ThreatKind.NONE)

    cache_key = (position.hash_key, move, player)
    cached = position.analysis_cache.get(cache_key)
    if isinstance(cached, ThreatProfile):
        return cached

    row, column = move
    position.board[row][column] = player
    try:
        if position.is_win_at(move, player):
            profile = ThreatProfile(ThreatKind.FIVE, winning_points=(move,))
            position.analysis_cache[cache_key] = profile
            return profile

        four_directions = 0
        open_four_directions = 0
        open_three_directions = 0
        closed_three_directions = 0
        open_two_directions = 0
        all_wins: set[Position] = set()

        for delta_row, delta_column in DIRECTIONS:
            wins = _winning_points_in_direction(
                position,
                move,
                player,
                delta_row,
                delta_column,
            )
            if wins:
                four_directions += 1
                all_wins.update(wins)
                if len(wins) >= 2:
                    open_four_directions += 1
                continue

            open_extensions, closed_extensions = _extension_counts(
                position,
                move,
                player,
                delta_row,
                delta_column,
            )
            if open_extensions:
                open_three_directions += 1
            elif closed_extensions:
                closed_three_directions += 1
            else:
                text = _direction_text(
                    position,
                    move,
                    player,
                    delta_row,
                    delta_column,
                )
                if any(pattern in text for pattern in (".XX.", ".X.X.", ".X..X.")):
                    open_two_directions += 1

        if four_directions >= 2:
            kind = ThreatKind.DOUBLE_FOUR
        elif open_four_directions:
            kind = ThreatKind.OPEN_FOUR
        elif four_directions and open_three_directions:
            kind = ThreatKind.FOUR_THREE
        elif four_directions:
            kind = ThreatKind.FOUR
        elif open_three_directions >= 2:
            kind = ThreatKind.DOUBLE_THREE
        elif open_three_directions:
            kind = ThreatKind.OPEN_THREE
        elif closed_three_directions:
            kind = ThreatKind.CLOSED_THREE
        elif open_two_directions:
            kind = ThreatKind.OPEN_TWO
        else:
            kind = ThreatKind.NONE

        profile = ThreatProfile(
            kind,
            four_directions,
            open_three_directions,
            closed_three_directions,
            open_two_directions,
            tuple(sorted(all_wins)),
        )
        position.analysis_cache[cache_key] = profile
        return profile
    finally:
        position.board[row][column] = 0


def move_potential(position: SearchPosition, move: Position, player: int) -> int:
    """Return a fast tactical score; exact labels come from :func:`analyze_move`."""

    if not position.is_legal(move):
        return -WIN_SCORE
    if position.is_winning_move(move, player):
        return WIN_SCORE

    direction_scores: list[int] = []
    for delta_row, delta_column in DIRECTIONS:
        line = _ordering_line(position, move, player, delta_row, delta_column)
        score = 0
        for value, patterns in _ORDERING_PATTERNS:
            if any(_pattern_through_anchor(line, pattern) for pattern in patterns):
                score = value
                break
        direction_scores.append(score)

    fours = sum(score >= 38_000 for score in direction_scores)
    threes = sum(score >= 10_000 for score in direction_scores)
    bonus = 0
    if fours >= 2:
        bonus = 180_000
    elif fours and threes >= 2:
        bonus = 100_000
    elif threes >= 2:
        bonus = 25_000
    return sum(direction_scores) + bonus
