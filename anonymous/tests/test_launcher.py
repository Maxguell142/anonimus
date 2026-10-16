import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run


class TestLauncher(unittest.TestCase):
    def test_gui_option_starts_desktop_application(self):
        with patch.object(sys, "argv", ["run.py", "--gui"]), patch(
            "anonymous.desktop.run_desktop"
        ) as run_desktop:
            run.main()

        run_desktop.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
