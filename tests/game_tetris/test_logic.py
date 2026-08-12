import random
import unittest
from dataclasses import replace

from games.game_tetris.config import BOARD_HEIGHT, BOARD_WIDTH, LOCK_DELAY_MS
from games.game_tetris.logic import (
    ActivePiece,
    advance_time,
    can_place,
    empty_board,
    ghost_y,
    hard_drop,
    hold_piece,
    move,
    new_game,
    rotate,
    soft_drop,
    toggle_pause,
)


def board_with_cells(filled):
    board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
    for column, row in filled:
        board[row][column] = 7
    return tuple(tuple(row) for row in board)


class TetrisLogicTests(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(7)

    def test_new_game_has_active_piece_and_five_previews(self):
        state = new_game(self.rng)
        self.assertEqual(state.status, "running")
        self.assertEqual(len(state.next_queue), 5)
        self.assertTrue(can_place(state.board, state.active))
        first_sequence = (state.active.kind,) + state.next_queue
        other = new_game(random.Random(7))
        self.assertEqual(first_sequence, (other.active.kind,) + other.next_queue)

    def test_horizontal_movement_stops_at_wall(self):
        state = replace(new_game(self.rng), active=ActivePiece("O", x=-1, y=4))
        self.assertEqual(move(state, -1).state, state)
        moved = move(state, 1).state
        self.assertEqual(moved.active.x, 0)

    def test_soft_and_hard_drop_award_distance_score(self):
        state = replace(new_game(self.rng), active=ActivePiece("O"))
        soft = soft_drop(state)
        self.assertEqual(soft.drop_distance, 1)
        self.assertEqual(soft.state.score, 1)
        hard = hard_drop(soft.state, self.rng)
        self.assertGreater(hard.drop_distance, 0)
        self.assertEqual(hard.state.score, 1 + hard.drop_distance * 2)
        self.assertIn("locked", hard.events)

    def test_ghost_matches_hard_drop_landing_position(self):
        state = replace(new_game(self.rng), active=ActivePiece("T"))
        expected_y = ghost_y(state)
        distance = hard_drop(state, self.rng).drop_distance
        self.assertEqual(state.active.y + distance, expected_y)

    def test_single_line_clear_scores_and_collapses_board(self):
        bottom = BOARD_HEIGHT - 1
        filled = ((column, bottom) for column in range(BOARD_WIDTH) if column not in range(3, 7))
        state = replace(
            new_game(self.rng),
            board=board_with_cells(filled),
            active=ActivePiece("I", rotation=0, x=3, y=bottom - 1),
        )
        result = hard_drop(state, self.rng)
        self.assertEqual(result.cleared_rows, (bottom,))
        self.assertEqual(result.state.lines, 1)
        self.assertEqual(result.state.score, 100)
        self.assertTrue(all(value == 0 for value in result.state.board[0]))

    def test_hold_can_only_be_used_once_before_locking(self):
        state = new_game(self.rng)
        current = state.active.kind
        next_piece = state.next_queue[0]
        first = hold_piece(state, self.rng).state
        self.assertEqual(first.hold, current)
        self.assertEqual(first.active.kind, next_piece)
        self.assertTrue(first.hold_used)
        self.assertEqual(hold_piece(first, self.rng).state, first)

        after_lock = hard_drop(first, self.rng).state
        self.assertFalse(after_lock.hold_used)
        swapped = hold_piece(after_lock, self.rng).state
        self.assertEqual(swapped.active.kind, current)

    def test_srs_kick_rotates_a_piece_away_from_left_wall(self):
        state = replace(new_game(self.rng), active=ActivePiece("T", rotation=1, x=-1, y=5))
        self.assertTrue(can_place(state.board, state.active))
        result = rotate(state, "counterclockwise")
        self.assertIn("rotated", result.events)
        self.assertEqual(result.state.active.rotation, 0)
        self.assertEqual(result.state.active.x, 0)

    def test_grounded_piece_locks_after_delay(self):
        state = replace(
            new_game(self.rng),
            active=ActivePiece("O", x=3, y=BOARD_HEIGHT - 2),
        )
        before = advance_time(state, LOCK_DELAY_MS - 1, self.rng)
        self.assertNotIn("locked", before.events)
        result = advance_time(before.state, 1, self.rng)
        self.assertIn("locked", result.events)
        self.assertNotEqual(result.state.active.kind, state.active.kind)

    def test_spawn_collision_after_hold_causes_game_over(self):
        state = replace(
            new_game(self.rng),
            board=board_with_cells(((4, 0),)),
            active=ActivePiece("I", x=3, y=10),
            hold="T",
        )
        result = hold_piece(state, self.rng)
        self.assertEqual(result.state.status, "game_over")
        self.assertIn("game_over", result.events)

    def test_pause_freezes_time_and_actions(self):
        state = new_game(self.rng)
        paused = toggle_pause(state)
        self.assertEqual(paused.status, "paused")
        self.assertEqual(advance_time(paused, 500, self.rng).state, paused)
        self.assertEqual(move(paused, 1).state, paused)
        self.assertEqual(toggle_pause(paused).status, "running")

    def test_invalid_time_is_rejected(self):
        with self.assertRaises(ValueError):
            advance_time(new_game(self.rng), -1, self.rng)

    def test_empty_board_shape_is_stable(self):
        board = empty_board()
        self.assertEqual(len(board), BOARD_HEIGHT)
        self.assertTrue(all(len(row) == BOARD_WIDTH for row in board))


if __name__ == "__main__":
    unittest.main()
