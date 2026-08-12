import tempfile
import unittest
from pathlib import Path

from games.common.json_store import (
    choice_or_default,
    is_non_negative_int,
    load_json_object,
    non_negative_int,
    save_json_object,
)


class CommonJsonStoreTests(unittest.TestCase):
    def test_json_object_round_trip_preserves_unicode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            payload = {"language": "中文", "score": 12}
            self.assertTrue(save_json_object(path, payload))
            self.assertEqual(load_json_object(path), payload)

    def test_missing_corrupt_and_non_object_json_return_none(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            self.assertIsNone(load_json_object(path))
            path.write_text("not json", encoding="utf-8")
            self.assertIsNone(load_json_object(path))
            path.write_text("[1, 2]", encoding="utf-8")
            self.assertIsNone(load_json_object(path))

    def test_unserializable_payload_fails_without_raising(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            self.assertFalse(save_json_object(path, {"value": object()}))

    def test_non_negative_integer_rejects_boolean_and_negative_values(self):
        self.assertTrue(is_non_negative_int(0))
        self.assertTrue(is_non_negative_int(42))
        self.assertFalse(is_non_negative_int(True))
        self.assertFalse(is_non_negative_int(-1))
        self.assertEqual(non_negative_int("12", default=7), 7)

    def test_choice_validation_handles_invalid_and_unhashable_values(self):
        allowed = {"light": 1, "dark": 2}
        self.assertEqual(choice_or_default("dark", allowed, "light"), "dark")
        self.assertEqual(choice_or_default("missing", allowed, "light"), "light")
        self.assertEqual(choice_or_default([], allowed, "light"), "light")


if __name__ == "__main__":
    unittest.main()
