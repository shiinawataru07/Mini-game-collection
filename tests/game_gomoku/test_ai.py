import unittest

from games.game_gomoku.ai import SearchLimits, choose_move, limits_for_difficulty
from games.game_gomoku.ai.position import SearchPosition
from games.game_gomoku.ai.zobrist import hash_board
from games.game_gomoku.logic import new_game, place_stone


def play(state, *positions):
    for position in positions:
        result = place_stone(state, position)
        if not result.placed:
            raise AssertionError(f"Could not place stone at {position}")
        state = result.state
    return state


class GomokuAiTests(unittest.TestCase):
    def test_empty_board_uses_center(self):
        result = choose_move(new_game(), SearchLimits(time_ms=50, max_depth=2))
        self.assertEqual(result.move, (7, 7))
        self.assertEqual(result.principal_variation, ((7, 7),))

    def test_search_position_make_and_unmake_restore_everything(self):
        state = play(new_game(), (7, 7), (7, 8), (8, 8))
        position = SearchPosition.from_state(state)
        original_board = [row[:] for row in position.board]
        original_player = position.current_player
        original_moves = position.moves[:]
        original_hash = position.hash_key

        position.make_move((6, 6))
        self.assertEqual(position.hash_key, hash_board(position.board, position.current_player))
        self.assertEqual(position.unmake_move(), (6, 6))

        self.assertEqual(position.board, original_board)
        self.assertEqual(position.current_player, original_player)
        self.assertEqual(position.moves, original_moves)
        self.assertEqual(position.hash_key, original_hash)

    def test_ai_finishes_an_immediate_win(self):
        state = play(
            new_game(),
            (7, 3),
            (0, 0),
            (7, 4),
            (0, 2),
            (7, 5),
            (0, 4),
            (7, 6),
            (1, 0),
        )
        result = choose_move(state, SearchLimits(time_ms=500, max_depth=3))
        self.assertIn(result.move, ((7, 2), (7, 7)))
        self.assertTrue(result.forced_win)

    def test_ai_blocks_the_only_immediate_loss(self):
        state = play(
            new_game(),
            (7, 3),
            (7, 2),
            (7, 4),
            (0, 0),
            (7, 5),
            (0, 2),
            (7, 6),
        )
        result = choose_move(state, SearchLimits(time_ms=500, max_depth=2))
        self.assertEqual(result.move, (7, 7))

    def test_fixed_depth_search_is_deterministic_and_non_mutating(self):
        state = play(new_game("ai"), (7, 7), (7, 8), (8, 8))
        limits = SearchLimits(time_ms=2_000, max_depth=2)
        first = choose_move(state, limits)
        second = choose_move(state, limits)
        self.assertEqual(first.move, second.move)
        self.assertEqual(first.score, second.score)
        self.assertEqual(state.board[6][6], 0)
        self.assertIn(first.move, first.principal_variation)

    def test_invalid_limits_are_rejected(self):
        with self.assertRaises(ValueError):
            SearchLimits(time_ms=0)
        with self.assertRaises(ValueError):
            SearchLimits(max_depth=0)
        with self.assertRaises(ValueError):
            SearchLimits(max_nodes=0)
        with self.assertRaises(ValueError):
            SearchLimits(vcf_depth=-1)
        with self.assertRaises(ValueError):
            SearchLimits(table_capacity=0)

    def test_difficulty_presets_increase_search_budget(self):
        easy = limits_for_difficulty("easy")
        normal = limits_for_difficulty("normal")
        expert = limits_for_difficulty("expert")
        self.assertLess(easy.time_ms, normal.time_ms)
        self.assertLess(normal.time_ms, expert.time_ms)
        self.assertLess(easy.vcf_depth, normal.vcf_depth)
        self.assertLess(normal.vcf_depth, expert.vcf_depth)

    def test_vcf_is_reported_as_a_forced_principal_variation(self):
        board = [[0] * 15 for _ in range(15)]
        for row, column in ((7, 5), (7, 6), (7, 7)):
            board[row][column] = 1
        state = new_game()
        state = state.__class__(
            tuple(tuple(row) for row in board),
            current_player=1,
            moves=((7, 5), (7, 6), (7, 7)),
        )
        result = choose_move(
            state,
            SearchLimits(time_ms=500, max_depth=1, vcf_depth=3),
        )
        self.assertTrue(result.forced_win)
        self.assertEqual(len(result.principal_variation), 3)

    def test_transposition_table_capacity_does_not_change_fixed_depth_score(self):
        state = play(new_game("ai"), (7, 7), (7, 8), (8, 8))
        tiny = choose_move(
            state,
            SearchLimits(
                time_ms=2_000,
                max_depth=2,
                vcf_depth=0,
                table_capacity=1,
            ),
        )
        large = choose_move(
            state,
            SearchLimits(
                time_ms=2_000,
                max_depth=2,
                vcf_depth=0,
                table_capacity=32_768,
            ),
        )
        self.assertEqual(tiny.depth, 2)
        self.assertEqual(large.depth, 2)
        self.assertEqual(tiny.score, large.score)
        self.assertEqual(tiny.move, large.move)


if __name__ == "__main__":
    unittest.main()
