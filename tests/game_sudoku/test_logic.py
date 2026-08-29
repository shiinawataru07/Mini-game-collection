import unittest
from dataclasses import replace

from games.game_sudoku.logic import (
    advance_time,
    apply_hint,
    clear_selected,
    conflicting_positions,
    move_selection,
    new_game,
    redo,
    select_cell,
    set_value,
    toggle_note_mode,
    toggle_pause,
    undo,
    wrong_positions,
)


def first_editable(state):
    return next(
        (row, column)
        for row in range(9)
        for column in range(9)
        if state.level.puzzle[row][column] == 0
    )


class SudokuLogicTests(unittest.TestCase):
    def test_new_game_keeps_selected_campaign_level(self):
        state = new_game("medium", 4)
        self.assertEqual(state.difficulty, "medium")
        self.assertEqual(state.level.number, 5)
        self.assertEqual(state.values, state.level.puzzle)

    def test_given_cells_cannot_be_changed(self):
        state = new_game()
        given = next(
            (row, column)
            for row in range(9)
            for column in range(9)
            if state.level.puzzle[row][column]
        )
        selected = select_cell(state, given)
        self.assertEqual(set_value(selected, 9).state, selected)
        self.assertEqual(clear_selected(selected).state, selected)

    def test_notes_values_errors_and_clear(self):
        state = new_game()
        position = first_editable(state)
        state = select_cell(state, position)
        noted = set_value(toggle_note_mode(state), 3)
        self.assertIn("note", noted.events)
        self.assertEqual(noted.state.notes[position[0]][position[1]], frozenset({3}))

        state = toggle_note_mode(noted.state)
        correct = state.level.solution[position[0]][position[1]]
        wrong = 1 if correct != 1 else 2
        result = set_value(state, wrong)
        self.assertIn("error", result.events)
        self.assertEqual(result.state.mistakes, 1)
        self.assertIn(position, wrong_positions(result.state))
        cleared = clear_selected(result.state)
        self.assertEqual(cleared.state.values[position[0]][position[1]], 0)

    def test_undo_and_redo_restore_board(self):
        state = new_game()
        position = first_editable(state)
        state = select_cell(state, position)
        value = state.level.solution[position[0]][position[1]]
        placed = set_value(state, value).state
        self.assertEqual(undo(placed).state.values, state.values)
        self.assertEqual(redo(undo(placed).state).state.values, placed.values)

    def test_hint_and_final_value_complete_the_level(self):
        state = new_game()
        position = first_editable(state)
        hinted = apply_hint(select_cell(state, position))
        self.assertIn("hint", hinted.events)
        self.assertEqual(hinted.state.hints_used, 1)

        values = [list(row) for row in state.level.solution]
        values[position[0]][position[1]] = 0
        almost_done = replace(
            state,
            values=tuple(tuple(row) for row in values),
            selected=position,
        )
        result = set_value(almost_done, state.level.solution[position[0]][position[1]])
        self.assertEqual(result.state.status, "won")
        self.assertIn("won", result.events)

    def test_conflicts_selection_and_pause_timer(self):
        state = new_game()
        editable = [
            (row, column)
            for row in range(9)
            for column in range(9)
            if state.level.puzzle[row][column] == 0
        ]
        pair = next(
            (first, second)
            for first in editable
            for second in editable
            if first < second and first[0] == second[0]
        )
        values = [list(row) for row in state.values]
        values[pair[0][0]][pair[0][1]] = 9
        values[pair[1][0]][pair[1][1]] = 9
        conflict_state = replace(state, values=tuple(tuple(row) for row in values))
        self.assertTrue(set(pair).issubset(conflicting_positions(conflict_state)))

        moved = move_selection(select_cell(state, (0, 0)), -1, -1)
        self.assertEqual(moved.selected, (8, 8))
        timed = advance_time(state, 500)
        self.assertEqual(timed.elapsed_ms, 500)
        paused = toggle_pause(timed)
        self.assertEqual(advance_time(paused, 500), paused)
        self.assertEqual(toggle_pause(paused).status, "playing")


if __name__ == "__main__":
    unittest.main()
