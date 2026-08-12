"""Tests for traditional Minesweeper mouse gestures."""

import unittest

from games.game_minesweeper.input import BoardMouseInput


class BoardMouseInputTests(unittest.TestCase):
    def test_single_clicks_execute_on_release(self):
        mouse = BoardMouseInput()
        self.assertIsNone(mouse.press(1, (2, 3), False))
        self.assertEqual(mouse.release(1, (2, 3)), "reveal")
        self.assertIsNone(mouse.press(3, (1, 4), False))
        self.assertEqual(mouse.release(3, (1, 4)), "mark")

    def test_both_buttons_on_number_trigger_one_chord(self):
        mouse = BoardMouseInput()
        self.assertIsNone(mouse.press(1, (2, 3), True))
        self.assertEqual(mouse.press(3, (2, 3), True), "chord")
        self.assertIsNone(mouse.release(1, (2, 3)))
        self.assertIsNone(mouse.release(3, (2, 3)))
        self.assertFalse(mouse.chord_consumed)

    def test_both_buttons_on_hidden_cell_suppress_individual_actions(self):
        mouse = BoardMouseInput()
        mouse.press(3, (2, 3), False)
        self.assertIsNone(mouse.press(1, (2, 3), False))
        self.assertIsNone(mouse.release(3, (2, 3)))
        self.assertIsNone(mouse.release(1, (2, 3)))

    def test_dragging_outside_cancels_a_click(self):
        mouse = BoardMouseInput()
        mouse.press(1, (2, 3), False)
        self.assertIsNone(mouse.release(1, None))

    def test_reset_clears_partial_gesture(self):
        mouse = BoardMouseInput()
        mouse.press(1, (2, 3), False)
        mouse.reset()
        self.assertIsNone(mouse.release(1, (2, 3)))


if __name__ == "__main__":
    unittest.main()
