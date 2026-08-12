import unittest

from games.game_tetris.input import HorizontalInput


class TetrisInputTests(unittest.TestCase):
    def test_press_moves_immediately_then_repeats_after_das(self):
        controls = HorizontalInput(das_ms=100, arr_ms=30)
        self.assertEqual(controls.press("left"), "left")
        self.assertEqual(controls.advance(99), ())
        self.assertEqual(controls.advance(1), ("left",))
        self.assertEqual(controls.advance(60), ("left", "left"))

    def test_last_pressed_direction_has_priority(self):
        controls = HorizontalInput()
        controls.press("left")
        self.assertEqual(controls.press("right"), "right")
        self.assertEqual(controls.active, "right")
        self.assertEqual(controls.release("right"), "left")
        self.assertEqual(controls.active, "left")

    def test_reset_and_invalid_time(self):
        controls = HorizontalInput()
        controls.press("right")
        controls.reset()
        self.assertIsNone(controls.active)
        with self.assertRaises(ValueError):
            controls.advance(-1)


if __name__ == "__main__":
    unittest.main()
