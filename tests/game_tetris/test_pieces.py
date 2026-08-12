import random
import unittest

from games.game_tetris.pieces import ALL_PIECES, SHAPES, cells, kick_offsets, shuffled_bag


class TetrisPieceTests(unittest.TestCase):
    def test_every_bag_contains_every_piece_once(self):
        rng = random.Random(42)
        for _ in range(20):
            bag = shuffled_bag(rng)
            self.assertEqual(len(bag), 7)
            self.assertEqual(set(bag), set(ALL_PIECES))

    def test_every_rotation_occupies_four_unique_cells(self):
        for kind, rotations in SHAPES.items():
            with self.subTest(kind=kind):
                self.assertEqual(len(rotations), 4)
                for rotation in range(4):
                    occupied = cells(kind, rotation, 3, 4)
                    self.assertEqual(len(occupied), 4)
                    self.assertEqual(len(set(occupied)), 4)

    def test_srs_kicks_always_test_original_position_first(self):
        for kind in ALL_PIECES:
            with self.subTest(kind=kind):
                self.assertEqual(kick_offsets(kind, 0, 1)[0], (0, 0))


if __name__ == "__main__":
    unittest.main()
