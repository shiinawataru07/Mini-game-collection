import unittest

from games.game_gomoku.ai.position import SearchPosition
from games.game_gomoku.ai.threats import find_vcf
from games.game_gomoku.logic import GameState


def position_with(
    black: tuple[tuple[int, int], ...],
    white: tuple[tuple[int, int], ...] = (),
) -> SearchPosition:
    board = [[0] * 15 for _ in range(15)]
    for row, column in black:
        board[row][column] = 1
    for row, column in white:
        board[row][column] = 2
    state = GameState(tuple(tuple(row) for row in board), 1, moves=black + white)
    return SearchPosition.from_state(state)


class GomokuVcfTests(unittest.TestCase):
    def test_open_three_has_a_provable_vcf(self):
        position = position_with(((7, 5), (7, 6), (7, 7)))
        original_board = [row[:] for row in position.board]
        original_hash = position.hash_key

        result = find_vcf(position, max_attacks=3)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(len(result.line), 3)
        for move in result.line:
            position.make_move(move)
        self.assertTrue(position.is_win_at(result.line[-1], 1))
        for _ in result.line:
            position.unmake_move()
        self.assertEqual(position.board, original_board)
        self.assertEqual(position.hash_key, original_hash)

    def test_vcf_chains_multiple_forcing_fours(self):
        position = position_with(
            ((7, 4), (7, 5), (7, 6), (4, 7), (5, 7)),
            ((7, 3),),
        )
        result = find_vcf(position, max_attacks=4)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(
            result.line,
            ((7, 7), (7, 8), (6, 7), (3, 7), (8, 7)),
        )

    def test_vcf_is_rejected_when_defender_can_win_first(self):
        position = position_with(
            ((7, 5), (7, 6), (7, 7), (2, 2)),
            ((2, 3), (2, 4), (2, 5), (2, 6)),
        )
        self.assertIsNone(find_vcf(position, max_attacks=4))

    def test_invalid_vcf_depth_is_rejected(self):
        with self.assertRaises(ValueError):
            find_vcf(position_with(((7, 7),)), max_attacks=0)


if __name__ == "__main__":
    unittest.main()
