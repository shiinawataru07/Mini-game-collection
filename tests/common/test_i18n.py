import unittest

from games.common.i18n import bind_translations, translate


class CommonI18nTests(unittest.TestCase):
    def setUp(self):
        self.translations = {
            "en": {"start": "Start"},
            "zh": {"start": "开始"},
        }

    def test_translate_reads_game_owned_catalog(self):
        self.assertEqual(translate(self.translations, "en", "start"), "Start")
        self.assertEqual(translate(self.translations, "zh", "start"), "开始")

    def test_bound_translator_keeps_existing_game_api(self):
        text = bind_translations(self.translations)
        self.assertEqual(text("zh", "start"), "开始")
        with self.assertRaises(KeyError):
            text("en", "missing")


if __name__ == "__main__":
    unittest.main()
