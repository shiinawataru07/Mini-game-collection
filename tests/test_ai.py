"""Tests for the Pygame-independent 2048 AI."""

import unittest

from games.game_2048.ai import (
    choose_move,
    evaluate_board,
    legal_moves,
    spawn_outcomes,
)


class AiTests(unittest.TestCase):
    def test_terminal_board_has_no_move(self):
        board = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ]
        self.assertIsNone(choose_move(board))

    def test_ai_returns_only_a_legal_move(self):
        board = [
            [2, 2, 4, 8],
            [16, 32, 64, 128],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        legal_directions = {direction for direction, _, _ in legal_moves(board)}
        self.assertIn(choose_move(board), legal_directions)

    def test_search_does_not_modify_the_input_board(self):
        board = [
            [2, 2, 0, 0],
            [4, 8, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        original = [row[:] for row in board]
        choose_move(board)
        self.assertEqual(board, original)

    def test_same_board_produces_a_stable_choice(self):
        board = [
            [2, 4, 8, 16],
            [4, 8, 16, 32],
            [2, 4, 8, 16],
            [0, 2, 4, 8],
        ]
        self.assertEqual(choose_move(board), choose_move(board))

    def test_spawn_outcomes_use_correct_probabilities(self):
        board = [
            [2, 4, 8, 16],
            [32, 64, 128, 256],
            [512, 1024, 2, 4],
            [8, 16, 32, 0],
        ]
        outcomes = spawn_outcomes(board)
        probabilities_by_value = {2: 0.0, 4: 0.0}
        for outcome, probability in outcomes:
            probabilities_by_value[outcome[3][3]] += probability
        self.assertAlmostEqual(sum(probability for _, probability in outcomes), 1.0)
        self.assertAlmostEqual(probabilities_by_value[2], 0.9)
        self.assertAlmostEqual(probabilities_by_value[4], 0.1)

    def test_evaluation_rewards_space_and_cornered_max_tile(self):
        spacious = [
            [128, 8, 4, 2],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        crowded = [
            [128, 8, 4, 2],
            [2, 4, 8, 16],
            [4, 8, 16, 32],
            [8, 16, 32, 64],
        ]
        centered_max = [
            [2, 8, 4, 0],
            [0, 128, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        self.assertGreater(evaluate_board(spacious), evaluate_board(crowded))
        self.assertGreater(evaluate_board(spacious), evaluate_board(centered_max))

    def test_invalid_depth_is_rejected(self):
        with self.assertRaises(ValueError):
            choose_move([[0] * 4 for _ in range(4)], depth=0)


if __name__ == "__main__":
    unittest.main()

