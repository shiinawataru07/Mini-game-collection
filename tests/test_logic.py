"""Tests for the Pygame-independent 2048 rules."""

import unittest

from games.game_2048.logic import (
    GameState,
    add_random_tile,
    apply_move,
    can_move,
    create_empty_board,
    merge_line,
    move_board,
    new_game,
)
from tests.support import FixedRandom


class MergeLineTests(unittest.TestCase):
    def test_common_merge_rules(self):
        cases = [
            ([0, 0, 0, 0], [0, 0, 0, 0], 0),
            ([2, 0, 2, 0], [4, 0, 0, 0], 4),
            ([2, 2, 2, 0], [4, 2, 0, 0], 4),
            ([2, 2, 2, 2], [4, 4, 0, 0], 8),
            ([4, 4, 8, 8], [8, 16, 0, 0], 24),
            ([4, 4, 8, 0], [8, 8, 0, 0], 8),
        ]
        for line, expected, score in cases:
            with self.subTest(line=line):
                self.assertEqual(merge_line(line), (expected, score))


class BoardMovementTests(unittest.TestCase):
    def setUp(self):
        self.board = [
            [2, 2, 0, 0],
            [4, 0, 4, 8],
            [0, 0, 8, 0],
            [0, 4, 0, 8],
        ]

    def test_moves_in_all_directions(self):
        cases = {
            "left": [[4, 0, 0, 0], [8, 8, 0, 0], [8, 0, 0, 0], [4, 8, 0, 0]],
            "right": [[0, 0, 0, 4], [0, 0, 8, 8], [0, 0, 0, 8], [0, 0, 4, 8]],
            "up": [[2, 2, 4, 16], [4, 4, 8, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            "down": [[0, 0, 0, 0], [0, 0, 0, 0], [2, 2, 4, 0], [4, 4, 8, 16]],
        }
        for direction, expected in cases.items():
            with self.subTest(direction=direction):
                moved, _, changed = move_board(self.board, direction)
                self.assertEqual(moved, expected)
                self.assertTrue(changed)

    def test_move_reports_score_without_changing_original(self):
        board = [[2, 2, 4, 4], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        moved, score, changed = move_board(board, "left")
        self.assertEqual(moved[0], [4, 8, 0, 0])
        self.assertEqual(score, 12)
        self.assertTrue(changed)
        self.assertEqual(board[0], [2, 2, 4, 4])

    def test_invalid_direction_is_rejected(self):
        with self.assertRaises(ValueError):
            move_board(create_empty_board(), "diagonal")


class GameStateTests(unittest.TestCase):
    def test_random_tile_can_be_two_or_four(self):
        board = create_empty_board()
        with_two = add_random_tile(board, FixedRandom(0.5))
        with_four = add_random_tile(board, FixedRandom(0.05))
        self.assertEqual(with_two[0][0], 2)
        self.assertEqual(with_four[0][0], 4)
        self.assertEqual(board[0][0], 0)

    def test_new_game_starts_with_two_tiles(self):
        state = new_game(rng=FixedRandom())
        tiles = [value for row in state.board for value in row if value]
        self.assertEqual(tiles, [2, 2])
        self.assertEqual(state.score, 0)
        self.assertFalse(state.game_over)

    def test_valid_move_adds_one_tile_and_updates_score(self):
        state = GameState(
            [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=10,
        )
        result = apply_move(state, "left", FixedRandom())
        tiles = [value for row in result.board for value in row if value]
        self.assertEqual(sorted(tiles), [2, 4])
        self.assertEqual(result.score, 14)

    def test_invalid_move_does_not_add_tile(self):
        state = GameState(
            [[2, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        )
        result = apply_move(state, "left", FixedRandom())
        self.assertEqual(result.board, state.board)
        self.assertEqual(result.score, 0)

    def test_game_over_detection(self):
        ended = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ]
        playable = [
            [2, 2, 4, 8],
            [4, 8, 16, 32],
            [8, 16, 32, 64],
            [16, 32, 64, 128],
        ]
        self.assertFalse(can_move(ended))
        self.assertTrue(can_move(playable))
        self.assertTrue(apply_move(GameState(ended), "left").game_over)

    def test_new_game_can_be_used_to_restart(self):
        restarted = new_game(size=2, rng=FixedRandom())
        self.assertEqual(restarted.score, 0)
        self.assertFalse(restarted.game_over)
        self.assertEqual(sum(value != 0 for row in restarted.board for value in row), 2)


if __name__ == "__main__":
    unittest.main()

