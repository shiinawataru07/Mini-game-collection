"""Tests for movement paths and tile-effect keyframes."""

import unittest

from games.game_2048.animation import (
    animation_tile_scales,
    build_move_animation,
    build_tile_motions,
    merge_pop_scale,
    spawn_pop_scale,
)
from games.game_2048.logic import GameState

from tests.support import FixedRandom


class MoveAnimationTests(unittest.TestCase):
    def test_each_existing_tile_gets_one_motion(self):
        board = [
            [2, 0, 2, 0],
            [4, 8, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 16],
        ]
        for direction in ("up", "down", "left", "right"):
            with self.subTest(direction=direction):
                self.assertEqual(len(build_tile_motions(board, direction)), 5)

    def test_merging_tiles_share_the_same_destination(self):
        board = [[2, 2, 2, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        motions = build_tile_motions(board, "left")
        self.assertEqual([motion.start for motion in motions], [(0, 0), (0, 1), (0, 2)])
        self.assertEqual([motion.end for motion in motions], [(0, 0), (0, 0), (0, 1)])

    def test_move_animation_identifies_merge_and_spawn_positions(self):
        state = GameState([[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        animation = build_move_animation(state, "left", 1000, FixedRandom())
        self.assertIsNotNone(animation)
        self.assertEqual(animation.merged_positions, frozenset({(0, 0)}))
        self.assertEqual(animation.spawned_position, (0, 1))
        self.assertEqual(animation.gained_score, 4)

    def test_invalid_move_does_not_create_animation(self):
        state = GameState([[2, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        self.assertIsNone(build_move_animation(state, "left", 0, FixedRandom()))

    def test_merge_and_spawn_scales_have_expected_keyframes(self):
        self.assertAlmostEqual(merge_pop_scale(0.0), 1.0)
        self.assertAlmostEqual(merge_pop_scale(0.5), 1.15)
        self.assertAlmostEqual(merge_pop_scale(1.0), 1.0)
        self.assertAlmostEqual(spawn_pop_scale(0.0), 0.0)
        self.assertAlmostEqual(spawn_pop_scale(0.7), 1.1)
        self.assertAlmostEqual(spawn_pop_scale(1.0), 1.0)

    def test_animation_scales_apply_to_merge_and_spawn_only(self):
        state = GameState([[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        animation = build_move_animation(state, "left", 0, FixedRandom())
        scales = animation_tile_scales(animation, 0.5)
        self.assertEqual(set(scales), {(0, 0), (0, 1)})
        self.assertGreater(scales[(0, 0)], 1.0)
        self.assertGreater(scales[(0, 1)], 0.0)


if __name__ == "__main__":
    unittest.main()
