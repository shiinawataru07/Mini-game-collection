import unittest

from games.game_tetris.animation import LineClearAnimation, animation_from_transition
from games.game_tetris.logic import Transition, new_game


class TetrisAnimationTests(unittest.TestCase):
    def test_line_clear_animation_has_bounded_progress(self):
        animation = LineClearAnimation((21,), 1000)
        self.assertEqual(animation.progress(900), 0.0)
        self.assertGreater(animation.progress(1090), 0.0)
        self.assertEqual(animation.progress(2000), 1.0)
        self.assertTrue(animation.finished(2000))

    def test_animation_only_created_for_cleared_rows(self):
        state = new_game()
        self.assertIsNone(animation_from_transition(Transition(state), 0))
        transition = Transition(state, ("lines_cleared",), (21,))
        self.assertIsNotNone(animation_from_transition(transition, 0))


if __name__ == "__main__":
    unittest.main()
