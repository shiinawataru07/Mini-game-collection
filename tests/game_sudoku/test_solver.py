import unittest

from games.game_sudoku.puzzles import CLUE_COUNTS, DIFFICULTY_ORDER, LEVELS
from games.game_sudoku.solver import candidates, count_solutions, grid_string, parse_grid, solve


class SudokuSolverTests(unittest.TestCase):
    def test_parser_and_candidates(self):
        grid = parse_grid(
            "530070000"
            "600195000"
            "098000060"
            "800060003"
            "400803001"
            "700020006"
            "060000280"
            "000419005"
            "000080079"
        )
        self.assertEqual(candidates(grid, (0, 2)), frozenset({1, 2, 4}))
        self.assertEqual(count_solutions(grid), 1)
        self.assertIsNotNone(solve(grid))

    def test_invalid_grid_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_grid("0" * 80)
        with self.assertRaises(ValueError):
            parse_grid("11" + "0" * 79)

    def test_campaign_has_sixty_unique_verified_levels(self):
        encoded_puzzles: set[str] = set()
        for difficulty in DIFFICULTY_ORDER:
            self.assertEqual(len(LEVELS[difficulty]), 20)
            for level in LEVELS[difficulty]:
                puzzle = grid_string(level.puzzle)
                self.assertNotIn(puzzle, encoded_puzzles)
                encoded_puzzles.add(puzzle)
                self.assertEqual(level.clue_count, CLUE_COUNTS[difficulty])
                self.assertEqual(count_solutions(level.puzzle), 1)
                self.assertEqual(solve(level.puzzle), level.solution)
        self.assertEqual(len(encoded_puzzles), 60)


if __name__ == "__main__":
    unittest.main()
