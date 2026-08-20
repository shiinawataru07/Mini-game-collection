import tempfile
import unittest
from pathlib import Path

import pygame
from games.common.app_settings import (
    AppSettings,
    apply_global_action,
    audio_status,
    global_action_from_key,
    load_app_settings,
    save_app_settings,
)


class AppSettingsTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            expected = AppSettings(volume=40, muted=True, fullscreen=True)
            self.assertTrue(save_app_settings(expected, path))
            self.assertEqual(load_app_settings(path), expected)

    def test_invalid_values_fall_back_or_are_clamped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(
                '{"volume": 900, "muted": "yes", "fullscreen": 1}',
                encoding="utf-8",
            )
            self.assertEqual(load_app_settings(path), AppSettings(volume=100))

    def test_volume_changes_unmute_and_stay_in_range(self):
        settings = AppSettings(volume=0, muted=True)
        self.assertEqual(
            apply_global_action(settings, "volume_up"),
            AppSettings(volume=10, muted=False),
        )
        self.assertEqual(apply_global_action(AppSettings(volume=100), "volume_up").volume, 100)
        self.assertEqual(apply_global_action(AppSettings(volume=0), "volume_down").volume, 0)

    def test_shortcuts_and_status(self):
        self.assertEqual(global_action_from_key(pygame.K_m), "mute")
        self.assertEqual(global_action_from_key(pygame.K_F11), "fullscreen")
        self.assertEqual(global_action_from_key(pygame.K_KP_PLUS), "volume_up")
        self.assertIsNone(global_action_from_key(pygame.K_a))
        self.assertEqual(audio_status(AppSettings(muted=True)), "静音")
        self.assertEqual(AppSettings(volume=25).effective_volume, 0.25)


if __name__ == "__main__":
    unittest.main()
