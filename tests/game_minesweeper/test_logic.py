"""Tests for Pygame-independent Minesweeper rules."""

import random
import unittest

from games.game_minesweeper.config import DIFFICULTIES
from games.game_minesweeper.logic import (
    Cell,
    GameState,
    advance_time,
    chord_cell,
    cycle_mark,
    neighbors,
    new_custom_game,
    new_game,
    place_mines,
    remaining_mines,
    reveal_cell,
    toggle_flag,
)


def prepared_state(
    width,
    height,
    mines,
    revealed=(),
    flagged=(),
    questioned=(),
):
    mines = set(mines)
    revealed = set(revealed)
    flagged = set(flagged)
    questioned = set(questioned)
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
            visibility = (
                "revealed"
                if position in revealed
                else "flagged"
                if position in flagged
                else "questioned"
                if position in questioned
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


class BoardCreationTests(unittest.TestCase):
    def test_custom_board_accepts_reasonable_limits(self):
        minimum = new_custom_game(8, 8, 1)
        maximum = new_custom_game(30, 20, 120)
        self.assertEqual((minimum.width, minimum.height, minimum.mine_count), (8, 8, 1))
        self.assertEqual(
            (maximum.width, maximum.height, maximum.mine_count),
            (30, 20, 120),
        )
        self.assertEqual(maximum.difficulty, "custom")

    def test_custom_board_rejects_invalid_dimensions_and_density(self):
        for values in ((7, 8, 1), (31, 8, 1), (8, 7, 1), (8, 21, 1), (8, 8, 17)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                new_custom_game(*values)

    def test_supported_difficulties_have_expected_dimensions(self):
        for difficulty, spec in DIFFICULTIES.items():
            with self.subTest(difficulty=difficulty):
                state = new_game(difficulty)
                self.assertEqual((state.width, state.height), (spec.width, spec.height))
                self.assertEqual(state.mine_count, spec.mines)
                self.assertFalse(state.mines_placed)
                self.assertEqual(state.status, "ready")

    def test_unknown_difficulty_is_rejected(self):
        with self.assertRaises(ValueError):
            new_game("impossible")

    def test_first_reveal_and_neighbors_are_safe(self):
        state = place_mines(new_game("beginner"), (4, 4), random.Random(12))
        safe = {(4, 4), *neighbors(state, (4, 4))}
        self.assertTrue(all(not state.board[row][column].has_mine for row, column in safe))
        self.assertEqual(
            sum(cell.has_mine for row in state.board for cell in row),
            state.mine_count,
        )

    def test_neighbor_numbers_match_the_placed_mines(self):
        state = place_mines(new_game("beginner"), (0, 0), random.Random(4))
        for row in range(state.height):
            for column in range(state.width):
                cell = state.board[row][column]
                if not cell.has_mine:
                    expected = sum(
                        state.board[r][c].has_mine for r, c in neighbors(state, (row, column))
                    )
                    self.assertEqual(cell.adjacent_mines, expected)

    def test_seeded_mine_placement_is_reproducible(self):
        first = place_mines(new_game(), (4, 4), random.Random(7))
        second = place_mines(new_game(), (4, 4), random.Random(7))
        self.assertEqual(first.board, second.board)


class PlayerActionTests(unittest.TestCase):
    def test_revealing_empty_area_cascades_and_wins(self):
        state = prepared_state(3, 3, {(2, 2)})
        result = reveal_cell(state, (0, 0))
        self.assertEqual(result.state.status, "won")
        self.assertEqual(result.state.revealed_count, 8)
        self.assertEqual(result.state.board[2][2].visibility, "flagged")

    def test_flagged_cell_cannot_be_revealed(self):
        flagged = cycle_mark(new_game(), (4, 4))
        result = reveal_cell(flagged, (4, 4), random.Random(1))
        self.assertIs(result.state, flagged)
        self.assertFalse(result.state.mines_placed)

    def test_marks_cycle_and_flags_can_exceed_mine_count(self):
        state = new_game()
        positions = [(row, column) for row in range(2) for column in range(6)]
        for position in positions:
            state = cycle_mark(state, position)
        self.assertEqual(state.flag_count, len(positions))
        self.assertEqual(remaining_mines(state), state.mine_count - len(positions))
        state = cycle_mark(state, positions[0])
        self.assertEqual(state.flag_count, len(positions) - 1)
        self.assertEqual(state.board[positions[0][0]][positions[0][1]].visibility, "questioned")
        state = cycle_mark(state, positions[0])
        self.assertEqual(state.board[positions[0][0]][positions[0][1]].visibility, "hidden")

    def test_question_mark_can_be_revealed_and_does_not_count_as_flag(self):
        state = prepared_state(3, 3, {(2, 2)}, questioned={(0, 0)})
        result = reveal_cell(state, (0, 0))
        self.assertEqual(result.state.status, "won")
        self.assertEqual(result.state.revealed_count, 8)
        self.assertEqual(result.state.flag_count, 1)

    def test_revealing_a_mine_loses(self):
        state = prepared_state(3, 3, {(0, 0)})
        result = reveal_cell(state, (0, 0))
        self.assertEqual(result.state.status, "lost")
        self.assertEqual(result.triggered_mine, (0, 0))
        self.assertEqual(result.state.exploded_cell, (0, 0))

    def test_chord_reveals_neighbors_with_correct_flag(self):
        state = prepared_state(3, 3, {(0, 0)}, revealed={(1, 1)}, flagged={(0, 0)})
        result = chord_cell(state, (1, 1))
        self.assertEqual(result.state.status, "won")
        self.assertEqual(result.state.revealed_count, 8)

    def test_chord_with_wrong_flag_triggers_unmarked_mine(self):
        state = prepared_state(3, 3, {(0, 0)}, revealed={(1, 1)}, flagged={(0, 1)})
        result = chord_cell(state, (1, 1))
        self.assertEqual(result.state.status, "lost")
        self.assertEqual(result.triggered_mine, (0, 0))

    def test_chord_requires_matching_flag_count(self):
        state = prepared_state(3, 3, {(0, 0)}, revealed={(1, 1)})
        result = chord_cell(state, (1, 1))
        self.assertIs(result.state, state)

    def test_chord_treats_question_mark_as_an_unrevealed_cell(self):
        state = prepared_state(
            3,
            3,
            {(0, 0)},
            revealed={(1, 1)},
            flagged={(0, 0)},
            questioned={(2, 2)},
        )
        result = chord_cell(state, (1, 1))
        self.assertEqual(result.state.status, "won")
        self.assertEqual(result.state.board[2][2].visibility, "revealed")

    def test_actions_after_game_end_do_nothing(self):
        state = prepared_state(2, 2, {(0, 0)})
        lost = reveal_cell(state, (0, 0)).state
        self.assertIs(reveal_cell(lost, (1, 1)).state, lost)
        self.assertIs(toggle_flag(lost, (1, 1)), lost)


class TimerTests(unittest.TestCase):
    def test_time_only_advances_while_running(self):
        ready = new_game()
        self.assertIs(advance_time(ready, 100), ready)
        running = place_mines(ready, (4, 4), random.Random(2))
        advanced = advance_time(running, 125)
        self.assertEqual(advanced.elapsed_ms, 125)
        lost = reveal_cell(prepared_state(2, 2, {(0, 0)}), (0, 0)).state
        self.assertIs(advance_time(lost, 100), lost)

    def test_negative_elapsed_time_is_rejected(self):
        with self.assertRaises(ValueError):
            advance_time(new_game(), -1)


if __name__ == "__main__":
    unittest.main()
