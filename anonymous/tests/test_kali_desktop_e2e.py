import os
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from tkinter import scrolledtext, ttk
from uuid import uuid4
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous import desktop
from anonymous.engines.ops.kali_forensics import kali_forensics_engine


class ConfirmingMessageBox:
    def __init__(self):
        self.calls = []
        self.parent = None

    def askyesno(self, title, message, parent=None):
        self.calls.append((title, message))
        self.parent = parent
        return True


class TestKaliDesktopEndToEnd(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk GUI requires an interactive desktop: {exc}")
        self.root.withdraw()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        if hasattr(self, "app") and self.root.winfo_exists():
            self.app._close()
        elif hasattr(self, "root") and self.root.winfo_exists():
            self.root.destroy()
        if hasattr(self, "temp_dir"):
            self.temp_dir.cleanup()

    def test_kali_start_confirmation_dispatches_and_renders_result(self):
        messagebox = ConfirmingMessageBox()
        calls = []

        def process_input(command, confirmed_by_user=False):
            calls.append((command, confirmed_by_user))
            if not confirmed_by_user:
                return {
                    "type": "confirmation_required",
                    "pending_message": "kali start",
                    "message": "Confirmar inicio de Kali forense",
                }
            return {"type": "status", "message": "Kali forense iniciado correctamente"}

        with (
            patch.object(desktop, "LAYOUT_PATH", Path(self.temp_dir.name) / "layout.json"),
            patch.object(desktop.DesktopApp, "_refresh_panels"),
            patch.object(desktop.dispatcher, "process_input", side_effect=process_input),
        ):
            self.app = desktop.DesktopApp(
                self.root,
                tk,
                ttk,
                scrolledtext,
                messagebox,
            )
            self.root.deiconify()
            self.root.update()
            self.app.command_entry.insert(0, "kali start")
            self.app.send_button.invoke()

            completed = tk.BooleanVar(master=self.root, value=False)

            def wait_for_result():
                output = self.app.assistant_output.get("1.0", "end")
                if (
                    len(calls) == 2
                    and "Kali forense iniciado correctamente" in output
                    and not self.app.busy
                ):
                    completed.set(True)
                elif self.root.winfo_exists():
                    self.root.after(25, wait_for_result)

            self.root.after(25, wait_for_result)
            self.root.after(5000, lambda: completed.set(True))
            self.root.wait_variable(completed)

        self.assertEqual(calls, [("kali start", False), ("kali start", True)])
        self.assertEqual(len(messagebox.calls), 1)
        self.assertIn("Confirmar inicio de Kali forense", messagebox.calls[0][1])
        self.assertIs(messagebox.parent, self.root)
        output = self.app.assistant_output.get("1.0", "end")
        self.assertIn("Kali forense iniciado correctamente", output)

    @unittest.skipUnless(
        os.getenv("ANONYMOUS_KALI_LIVE_TESTS") == "1",
        "Set ANONYMOUS_KALI_LIVE_TESTS=1 to run the real GUI-to-Docker flow.",
    )
    def test_gui_runs_live_forensic_identification_through_docker(self):
        status = kali_forensics_engine.status()
        if not status["connected"] or not status["evidence_read_only"]:
            self.skipTest(f"Kali with read-only evidence mount is unavailable: {status['detail']}")

        filename = f"anonymous-live-gui-{uuid4().hex}.txt"
        evidence = kali_forensics_engine.evidence_dir / filename
        evidence.write_text("Synthetic GUI forensic integration fixture\n", encoding="utf-8")
        try:
            with (
                patch.object(desktop, "LAYOUT_PATH", Path(self.temp_dir.name) / "layout.json"),
                patch.object(desktop.DesktopApp, "_refresh_panels"),
            ):
                self.app = desktop.DesktopApp(
                    self.root,
                    tk,
                    ttk,
                    scrolledtext,
                    ConfirmingMessageBox(),
                )
                self.root.deiconify()
                self.root.update()
                self.app.command_entry.insert(0, f"kali forensic identify {filename}")
                self.app.send_button.invoke()

                completed = tk.BooleanVar(master=self.root, value=False)

                def wait_for_result():
                    output = self.app.assistant_output.get("1.0", "end")
                    if (
                        "Kali forensics · identify" in output
                        and "ASCII text" in output
                        and not self.app.busy
                    ):
                        completed.set(True)
                    elif self.root.winfo_exists():
                        self.root.after(25, wait_for_result)

                self.root.after(25, wait_for_result)
                self.root.after(10000, lambda: completed.set(True))
                self.root.wait_variable(completed)

            output = self.app.assistant_output.get("1.0", "end")
            self.assertIn("Kali forensics · identify", output)
            self.assertIn("ASCII text", output)
        finally:
            evidence.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
