"""Tests for the pure Snake rules."""

import unittest

from games.game_snake.config import FOOD_SCORE, move_interval_ms, moves_per_second
from games.game_snake.logic import GameState, advance, change_direction, new_game, spawn_food


class FirstChoiceRandom:
    def choice(self, values):
        return values[0]


class SnakeLogicTests(unittest.TestCase):
    def test_new_game_has_a_snake_and_food_on_an_empty_cell(self):
        state = new_game(rng=FirstChoiceRandom())
        self.assertEqual(len(state.snake), 4)
        self.assertNotIn(state.food, state.snake)
        self.assertEqual(state.status, "ready")

    def test_board_too_small_is_rejected(self):
        with self.assertRaises(ValueError):
            new_game(width=4, height=3)
        with self.assertRaises(ValueError):
            new_game(mode="unknown")

    def test_new_game_keeps_the_selected_mode(self):
        self.assertEqual(new_game(mode="classic").mode, "classic")
        self.assertEqual(new_game(mode="wrap").mode, "wrap")

    def test_reverse_direction_is_ignored(self):
        self.assertEqual(change_direction("right", "left"), "right")
        self.assertEqual(change_direction("right", "up"), "up")

    def test_normal_step_moves_without_growing(self):
        state = GameState(8, 6, ((3, 2), (2, 2), (1, 2)), "right", (7, 5), status="running")
        result = advance(state)
        self.assertEqual(result.state.snake, ((4, 2), (3, 2), (2, 2)))
        self.assertFalse(result.ate_food)

    def test_eating_food_grows_and_scores(self):
        state = GameState(8, 6, ((3, 2), (2, 2), (1, 2)), "right", (4, 2), status="running")
        result = advance(state, FirstChoiceRandom())
        self.assertTrue(result.ate_food)
        self.assertEqual(len(result.state.snake), 4)
        self.assertEqual(result.state.score, FOOD_SCORE)
        self.assertNotIn(result.state.food, result.state.snake)

    def test_wall_and_body_collisions_end_the_classic_game(self):
        wall = GameState(5, 5, ((4, 2), (3, 2)), "right", (0, 0), status="running")
        self.assertEqual(advance(wall).collision, "wall")

        body = GameState(5, 5, ((2, 1), (2, 2), (1, 2), (1, 1)), "down", (4, 4), status="running")
        result = advance(body)
        self.assertEqual(result.collision, "self")
        self.assertEqual(result.state.status, "game_over")

    def test_wrap_mode_enters_from_the_opposite_edge(self):
        horizontal = GameState(
            5, 5, ((4, 2), (3, 2)), "right", (2, 4), status="running", mode="wrap"
        )
        self.assertEqual(advance(horizontal).state.snake[0], (0, 2))

        vertical = GameState(
            5, 5, ((2, 0), (2, 1)), "up", (4, 4), status="running", mode="wrap"
        )
        self.assertEqual(advance(vertical).state.snake[0], (2, 4))

    def test_moving_into_the_departing_tail_is_legal(self):
        state = GameState(5, 5, ((2, 1), (2, 2), (1, 2), (1, 1)), "left", (4, 4), status="running")
        result = advance(state)
        self.assertIsNone(result.collision)
        self.assertEqual(result.state.snake[0], (1, 1))

    def test_filling_the_board_wins(self):
        state = GameState(2, 2, ((0, 0), (0, 1), (1, 1)), "right", (1, 0), status="running")
        result = advance(state)
        self.assertEqual(result.state.status, "won")
        self.assertIsNone(result.state.food)

    def test_spawn_food_returns_none_for_a_full_board(self):
        self.assertIsNone(spawn_food(2, 2, ((0, 0), (1, 0), (0, 1), (1, 1))))

    def test_speed_levels_are_fixed_and_ordered(self):
        self.assertEqual(moves_per_second("slow"), 5.0)
        self.assertEqual(moves_per_second("normal"), 8.0)
        self.assertEqual(moves_per_second("fast"), 12.0)
        self.assertGreater(move_interval_ms("slow"), move_interval_ms("fast"))


if __name__ == "__main__":
    unittest.main()
