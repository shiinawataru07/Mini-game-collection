"""Tests for deterministic Minesweeper solving, generation, and hints."""

import random
import unittest
from unittest.mock import patch

from games.game_minesweeper.logic import (
    Cell,
    GameState,
    new_custom_game,
    new_game,
    place_mines,
)
from games.game_minesweeper.solver import (
    deduce,
    find_hint,
    solve_from_first_reveal,
)


def state_from_cells(
    width,
    height,
    mines,
    revealed=(),
    flagged=(),
    adjacent_overrides=None,
):
    mines = set(mines)
    revealed = set(revealed)
    flagged = set(flagged)
    adjacent_overrides = adjacent_overrides or {}
    rows = []
    for row in range(height):
        cells = []
        for column in range(width):
            position = (row, column)
            adjacent = sum(
                (neighbor_row, neighbor_column) in mines
                for neighbor_row in range(max(0, row - 1), min(height, row + 2))
                for neighbor_column in range(max(0, column - 1), min(width, column + 2))
                if (neighbor_row, neighbor_column) != position
            )
            adjacent = adjacent_overrides.get(position, adjacent)
            visibility = (
                "revealed"
                if position in revealed
                else "flagged"
                if position in flagged
                else "hidden"
            )
            cells.append(Cell(position in mines, adjacent, visibility))
        rows.append(tuple(cells))
    return GameState(
        width=width,
        height=height,
        mine_count=len(mines),
        board=tuple(rows),
        status="running",
        mines_placed=True,
        revealed_count=len(revealed),
        flag_count=len(flagged),
    )


class DeductionTests(unittest.TestCase):
    def test_direct_rule_finds_a_mine(self):
        state = state_from_cells(
            2,
            2,
            {(0, 0)},
            revealed={(0, 1), (1, 0), (1, 1)},
        )
        deductions = deduce(state)
        self.assertEqual(deductions.mines, {(0, 0)})
        self.assertFalse(deductions.contradiction)

    def test_flag_satisfying_number_makes_other_neighbors_safe(self):
        state = state_from_cells(
            2,
            2,
            {(0, 0)},
            revealed={(1, 1)},
            flagged={(0, 0)},
        )
        deductions = deduce(state)
        self.assertEqual(deductions.safe, {(0, 1), (1, 0)})

    def test_subset_rule_derives_safe_difference(self):
        unknown = {(0, 1), (1, 0), (2, 2)}
        revealed = {
            (row, column) for row in range(3) for column in range(3) if (row, column) not in unknown
        }
        state = state_from_cells(
            3,
            3,
            {(0, 1)},
            revealed=revealed,
            adjacent_overrides={(0, 0): 1, (1, 1): 1},
        )
        deductions = deduce(state)
        self.assertIn((2, 2), deductions.safe)

    def test_conflicting_flags_are_reported_as_a_contradiction(self):
        state = state_from_cells(
            2,
            2,
            {(0, 0)},
            revealed={(1, 1)},
            flagged={(0, 1), (1, 0)},
        )
        self.assertTrue(deduce(state).contradiction)


class SolvableGenerationTests(unittest.TestCase):
    def test_generated_boards_are_solved_without_guessing(self):
        cases = {
            "beginner": (4, 4),
            "intermediate": (8, 8),
            "expert": (8, 15),
        }
        for difficulty, first_reveal in cases.items():
            with self.subTest(difficulty=difficulty):
                state = place_mines(
                    new_game(difficulty),
                    first_reveal,
                    random.Random(9),
                )
                self.assertTrue(solve_from_first_reveal(state, first_reveal))

    def test_generation_retries_rejected_layouts(self):
        with patch(
            "games.game_minesweeper.solver.solve_from_first_reveal",
            side_effect=(False, True),
        ) as solve:
            state = place_mines(new_game(), (4, 4), random.Random(3))
        self.assertTrue(state.mines_placed)
        self.assertEqual(solve.call_count, 2)

    def test_custom_board_is_also_verified_as_no_guess(self):
        first_reveal = (6, 9)
        state = place_mines(
            new_custom_game(20, 14, 55),
            first_reveal,
            random.Random(12),
        )
        self.assertTrue(solve_from_first_reveal(state, first_reveal))


class HintTests(unittest.TestCase):
    def test_ready_hint_points_to_safe_center_first_click(self):
        hint = find_hint(new_game("intermediate"))
        self.assertIsNotNone(hint)
        self.assertEqual(hint.kind, "safe")
        self.assertEqual(hint.position, (8, 8))

    def test_hint_can_identify_safe_and_mined_cells(self):
        mine_state = state_from_cells(
            2,
            2,
            {(0, 0)},
            revealed={(0, 1), (1, 0), (1, 1)},
        )
        safe_state = state_from_cells(
            2,
            2,
            {(0, 0)},
            revealed={(1, 1)},
            flagged={(0, 0)},
        )
        self.assertEqual(find_hint(mine_state).kind, "mine")
        self.assertEqual(find_hint(mine_state).position, (0, 0))
        self.assertEqual(find_hint(safe_state).kind, "safe")
        self.assertIn(find_hint(safe_state).position, {(0, 1), (1, 0)})

    def test_hint_points_out_an_incorrect_flag(self):
        state = state_from_cells(
            2,
            2,
            {(0, 0)},
            revealed={(1, 1)},
            flagged={(0, 1), (1, 0)},
        )
        hint = find_hint(state)
        self.assertEqual(hint.kind, "incorrect_flag")
        self.assertEqual(hint.position, (0, 1))


if __name__ == "__main__":
    unittest.main()
