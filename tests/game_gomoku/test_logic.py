import unittest

from games.game_gomoku.config import BOARD_SIZE
from games.game_gomoku.logic import new_game, place_stone, undo


def play(state, *positions):
    for position in positions:
        result = place_stone(state, position)
        if not result.placed:
            raise AssertionError(f"Could not place stone at {position}")
        state = result.state
    return state


class GomokuLogicTests(unittest.TestCase):
    def test_new_game_has_empty_board_and_black_starts(self):
        state = new_game()
        self.assertEqual(len(state.board), BOARD_SIZE)
        self.assertTrue(all(cell == 0 for row in state.board for cell in row))
        self.assertEqual(state.current_player, 1)
        self.assertEqual(state.status, "playing")

    def test_invalid_mode_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            new_game("network")  # type: ignore[arg-type]

    def test_players_alternate_and_occupied_point_is_ignored(self):
        state = play(new_game(), (7, 7))
        self.assertEqual(state.current_player, 2)
        result = place_stone(state, (7, 7))
        self.assertFalse(result.placed)
        self.assertIs(result.state, state)

    def test_out_of_bounds_move_is_ignored(self):
        state = new_game()
        self.assertFalse(place_stone(state, (-1, 0)).placed)
        self.assertFalse(place_stone(state, (BOARD_SIZE, 0)).placed)

    def test_horizontal_five_wins_for_black(self):
        state = play(
            new_game(),
            (7, 3),
            (0, 0),
            (7, 4),
            (0, 1),
            (7, 5),
            (0, 2),
            (7, 6),
            (0, 3),
            (7, 7),
        )
        self.assertEqual(state.status, "black_won")
        self.assertEqual(state.winning_line, tuple((7, column) for column in range(3, 8)))

    def test_vertical_five_wins_for_white(self):
        state = play(
            new_game(),
            (0, 0),
            (4, 8),
            (0, 2),
            (5, 8),
            (0, 4),
            (6, 8),
            (1, 6),
            (7, 8),
            (2, 10),
            (8, 8),
        )
        self.assertEqual(state.status, "white_won")

    def test_both_diagonal_directions_can_win(self):
        cases = (
            ((3, 3), (4, 4), (5, 5), (6, 6), (7, 7)),
            ((3, 10), (4, 9), (5, 8), (6, 7), (7, 6)),
        )
        fillers = ((14, 0), (14, 2), (14, 4), (14, 6))
        for diagonal in cases:
            with self.subTest(diagonal=diagonal):
                moves = []
                for index, position in enumerate(diagonal):
                    moves.append(position)
                    if index < len(fillers):
                        moves.append(fillers[index])
                state = play(new_game(), *moves)
                self.assertEqual(state.status, "black_won")

    def test_moves_after_game_end_are_ignored(self):
        state = play(
            new_game(),
            (7, 3),
            (0, 0),
            (7, 4),
            (0, 1),
            (7, 5),
            (0, 2),
            (7, 6),
            (0, 3),
            (7, 7),
        )
        result = place_stone(state, (8, 8))
        self.assertFalse(result.placed)
        self.assertIs(result.state, state)

    def test_local_undo_removes_one_move_and_restores_finished_game(self):
        state = play(
            new_game(),
            (7, 3),
            (0, 0),
            (7, 4),
            (0, 1),
            (7, 5),
            (0, 2),
            (7, 6),
            (0, 3),
            (7, 7),
        )
        restored = undo(state)
        self.assertEqual(restored.status, "playing")
        self.assertEqual(restored.current_player, 1)
        self.assertEqual(restored.board[7][7], 0)
        self.assertEqual(len(restored.moves), 8)

    def test_ai_mode_undo_is_ready_to_remove_a_turn_pair(self):
        state = play(new_game("ai"), (7, 7), (7, 8))
        restored = undo(state)
        self.assertFalse(restored.moves)
        self.assertEqual(restored.current_player, 1)


if __name__ == "__main__":
    unittest.main()
