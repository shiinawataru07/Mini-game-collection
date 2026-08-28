import json
import tempfile
import unittest
from pathlib import Path

from games.game_snake.maps import (
    BUILTIN_MAPS,
    MAP_FORMAT,
    MAP_VERSION,
    EditorState,
    MapFormatError,
    SnakeMap,
    clear_editor,
    discover_maps,
    editor_to_map,
    export_map,
    import_map_file,
    load_map,
    protected_cells,
    toggle_editor_wall,
    validate_map,
)


class SnakeMapTests(unittest.TestCase):
    def test_all_builtin_maps_are_connected_and_keep_spawn_clear(self):
        self.assertGreaterEqual(len(BUILTIN_MAPS), 4)
        for game_map in BUILTIN_MAPS:
            with self.subTest(game_map=game_map.name):
                self.assertEqual(validate_map(game_map), game_map)
                self.assertFalse(game_map.walls & protected_cells(game_map.width, game_map.height))

    def test_json_map_round_trip_and_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            expected = SnakeMap("测试地图", 12, 8, frozenset({(1, 1), (1, 2)}), "玩家")
            path = export_map(expected, folder, "test.snake-map.json")
            self.assertEqual(load_map(path), expected)
            maps, errors = discover_maps(folder)
            self.assertEqual(maps, (expected,))
            self.assertFalse(errors)

    def test_import_copies_a_valid_external_map(self):
        with tempfile.TemporaryDirectory() as source_directory:
            with tempfile.TemporaryDirectory() as target_directory:
                source = Path(source_directory) / "shared.json"
                expected = SnakeMap("分享地图", 12, 8, frozenset({(1, 1)}))
                export_map(expected, Path(source_directory), source.name)
                imported, destination = import_map_file(source, Path(target_directory))
                self.assertEqual(imported, expected)
                self.assertTrue(destination.exists())
                self.assertEqual(load_map(destination), expected)

    def test_malformed_version_coordinates_and_disconnected_areas_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            payload = {
                "format": MAP_FORMAT,
                "version": MAP_VERSION + 1,
                "name": "bad",
                "width": 12,
                "height": 8,
                "walls": [],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(MapFormatError):
                load_map(path)

        with self.assertRaises(MapFormatError):
            validate_map(SnakeMap("越界", 12, 8, frozenset({(12, 0)})))

        dividing_wall = frozenset((1, row) for row in range(8))
        with self.assertRaisesRegex(MapFormatError, "连通"):
            validate_map(SnakeMap("断开", 12, 8, dividing_wall))

    def test_editor_protects_spawn_and_can_toggle_clear_and_build_map(self):
        editor = EditorState("编辑测试", 12, 8)
        protected = next(iter(protected_cells(12, 8)))
        unchanged = toggle_editor_wall(editor, protected)
        self.assertFalse(unchanged.walls)
        self.assertIn("出生区", unchanged.message)

        edited = toggle_editor_wall(editor, (1, 1))
        self.assertEqual(edited.walls, frozenset({(1, 1)}))
        self.assertEqual(editor_to_map(edited).walls, edited.walls)
        self.assertFalse(clear_editor(edited).walls)


if __name__ == "__main__":
    unittest.main()
