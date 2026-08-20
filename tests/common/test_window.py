import unittest
from unittest.mock import patch

import pygame
from games.common import window


class WindowTests(unittest.TestCase):
    @patch("games.common.window.pygame.display.set_mode")
    @patch("games.common.window.pygame.display.set_caption")
    def test_open_window_honors_fullscreen(self, set_caption, set_mode):
        window.open_resizable_window((800, 600), "Game", fullscreen=True)
        set_caption.assert_called_once_with("Game")
        set_mode.assert_called_once_with((0, 0), pygame.FULLSCREEN)

    @patch("games.common.window.pygame.display.get_surface", return_value=None)
    @patch("games.common.window.pygame.display.set_mode")
    def test_leave_fullscreen_restores_windowed_size(self, set_mode, _get_surface):
        window._windowed_size = (820, 700)
        window.set_fullscreen(False, (560, 520))
        set_mode.assert_called_once_with((820, 700), pygame.RESIZABLE)


if __name__ == "__main__":
    unittest.main()
