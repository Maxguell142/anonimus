import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.desktop_layout import (
    DEFAULT_LAYOUT,
    PANEL_SPECS,
    load_layout,
    load_visible_panels,
    move_panel,
    resize_panel,
    save_layout,
)


class TestDesktopLayout(unittest.TestCase):
    def test_dashboard_uses_real_monitoring_and_activity_panels(self):
        self.assertIn("system", PANEL_SPECS)
        self.assertIn("matrix", PANEL_SPECS)
        self.assertIn("pipes", PANEL_SPECS)
        self.assertIn("events", PANEL_SPECS)
        self.assertIn("assistant", PANEL_SPECS)
        self.assertIn("findings", PANEL_SPECS)
        self.assertNotIn("reactor", PANEL_SPECS)
        self.assertNotIn("objectives", PANEL_SPECS)
        self.assertNotIn("countermeasures", PANEL_SPECS)
        self.assertEqual(set(DEFAULT_LAYOUT), set(PANEL_SPECS))

    def test_panels_can_be_moved_and_resized_without_affecting_others(self):
        moved = move_panel(DEFAULT_LAYOUT, "system", 640, 310)
        resized = resize_panel(moved, "system", 520, 360)
        self.assertEqual(moved["system"][:2], (640, 310))
        self.assertEqual(resized["system"], (640, 310, 520, 360))
        self.assertEqual(resized["matrix"], DEFAULT_LAYOUT["matrix"])

    def test_layout_changes_persist_between_runs(self):
        moved = move_panel(DEFAULT_LAYOUT, "pipes", 715, 110)
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "layout.json"
            visible = {"system", "matrix", "events", "assistant"}
            save_layout(file_path, moved, visible)
            restored = load_layout(file_path)
            restored_visibility = load_visible_panels(file_path)
        self.assertEqual(restored, moved)
        self.assertEqual(restored_visibility, visible)

    def test_panel_ids_and_minimum_dimensions_are_validated(self):
        with self.assertRaises(KeyError):
            move_panel(DEFAULT_LAYOUT, "missing", 10, 10)
        with self.assertRaises(ValueError):
            resize_panel(DEFAULT_LAYOUT, "system", 100, 20)


if __name__ == "__main__":
    unittest.main()
