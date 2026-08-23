import unittest

from games.game_gomoku.ai.patterns import ThreatKind, analyze_move
from games.game_gomoku.ai.position import SearchPosition
from games.game_gomoku.logic import GameState


def position_with(
    black: tuple[tuple[int, int], ...],
    white: tuple[tuple[int, int], ...] = (),
    current_player: int = 1,
) -> SearchPosition:
    board = [[0] * 15 for _ in range(15)]
    for row, column in black:
        board[row][column] = 1
    for row, column in white:
        board[row][column] = 2
    state = GameState(
        tuple(tuple(row) for row in board),
        current_player,  # type: ignore[arg-type]
        moves=black + white,
    )
    return SearchPosition.from_state(state)


class GomokuPatternTests(unittest.TestCase):
    def test_open_and_closed_four_are_distinguished_by_real_winning_points(self):
        open_four = analyze_move(
            position_with(((7, 4), (7, 5), (7, 6))),
            (7, 7),
            1,
        )
        closed_four = analyze_move(
            position_with(((7, 4), (7, 5), (7, 6)), ((7, 3),)),
            (7, 7),
            1,
        )
        self.assertEqual(open_four.kind, ThreatKind.OPEN_FOUR)
        self.assertEqual(open_four.winning_points, ((7, 3), (7, 8)))
        self.assertEqual(closed_four.kind, ThreatKind.FOUR)
        self.assertEqual(closed_four.winning_points, ((7, 8),))

    def test_compound_threats_are_classified(self):
        cases = (
            (
                ((7, 4), (7, 5), (7, 6), (4, 7), (5, 7), (6, 7)),
                (),
                ThreatKind.DOUBLE_FOUR,
            ),
            (
                ((7, 4), (7, 5), (7, 6), (5, 7), (6, 7)),
                ((7, 3),),
                ThreatKind.FOUR_THREE,
            ),
            (
                ((7, 5), (7, 6), (5, 7), (6, 7)),
                (),
                ThreatKind.DOUBLE_THREE,
            ),
        )
        for black, white, expected in cases:
            with self.subTest(expected=expected):
                profile = analyze_move(position_with(black, white), (7, 7), 1)
                self.assertEqual(profile.kind, expected)

    def test_edge_block_prevents_false_open_four(self):
        profile = analyze_move(
            position_with(((0, 0), (0, 1), (0, 2))),
            (0, 3),
            1,
        )
        self.assertEqual(profile.kind, ThreatKind.FOUR)
        self.assertEqual(profile.winning_points, ((0, 4),))


if __name__ == "__main__":
    unittest.main()
