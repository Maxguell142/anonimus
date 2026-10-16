import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.desktop import MODE_CONFIG, DesktopApp


class FakeWidget:
    def __init__(self):
        self.options = {}
        self.content = []

    def configure(self, **options):
        self.options.update(options)

    config = configure

    def insert(self, _where, text, *_tags):
        self.content.append(text)

    def see(self, _where):
        pass

    def tag_configure(self, _tag, **_options):
        pass


class TestDesktopModes(unittest.TestCase):
    def test_all_five_modes_have_required_titles_and_color_identity(self):
        expected = {
            "normal": ("ANONYMOUS // CENTRO DE CONTROL", "#73e8c5"),
            "attack": ("SISTEMA OFENSIVO // ENLACE TÁCTICO", "#bd83ff"),
            "defense": ("PROTOCOLOS DE DEFENSA ACTIVADOS", "#ff5964"),
            "success": ("TAREA COMPLETADA CON ÉXITO", "#9eff6e"),
            "error": ("ERROR CRÍTICO // FALLO EN SISTEMA", "#ff654f"),
        }
        self.assertEqual(set(MODE_CONFIG), set(expected))
        for mode, (title, accent) in expected.items():
            with self.subTest(mode=mode):
                self.assertEqual(MODE_CONFIG[mode]["title"], title)
                self.assertEqual(MODE_CONFIG[mode]["accent"], accent)

    def test_defense_events_use_red_alert_color(self):
        self.assertEqual(MODE_CONFIG["defense"]["event_color"], "#ff5964")
        self.assertEqual(MODE_CONFIG["defense"]["alert"], True)

    def test_product_identity_is_anonymous_not_jarvis(self):
        self.assertNotIn("jarvis", MODE_CONFIG["normal"]["title"].lower())

    def test_selecting_mode_updates_title_and_active_navigation(self):
        app = DesktopApp.__new__(DesktopApp)
        app.root = FakeWidget()
        app.hero_title = FakeWidget()
        app.event_log = FakeWidget()
        app.mode_buttons = {name: FakeWidget() for name in MODE_CONFIG}
        app.panel_title_labels = {}
        app.current_mode = None

        app.set_mode("attack")

        self.assertEqual(app.current_mode, "attack")
        self.assertEqual(app.hero_title.options["text"], MODE_CONFIG["attack"]["title"])
        self.assertEqual(app.mode_buttons["attack"].options["bg"], MODE_CONFIG["attack"]["accent"])
        self.assertNotEqual(app.mode_buttons["normal"].options["bg"], MODE_CONFIG["attack"]["accent"])


if __name__ == "__main__":
    unittest.main()
