import unittest

from games.common.app_settings_ui import app_settings_controls


class AppSettingsUiTests(unittest.TestCase):
    def test_controls_are_distinct_and_inside_modal(self):
        for window_size in ((600, 480), (760, 600), (1200, 800)):
            with self.subTest(window_size=window_size):
                controls = app_settings_controls(window_size)
                clickable = (
                    controls.close,
                    controls.volume_down,
                    controls.volume_up,
                    controls.mute,
                    controls.fullscreen,
                )
                self.assertTrue(all(controls.modal.contains(rect) for rect in clickable))
                for index, rect in enumerate(clickable):
                    for other in clickable[index + 1 :]:
                        self.assertFalse(rect.colliderect(other))


if __name__ == "__main__":
    unittest.main()
