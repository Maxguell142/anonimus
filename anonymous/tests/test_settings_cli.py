import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from rich.console import Console

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous import cli
from anonymous.settings import default_settings


class TestSettingsCLI(unittest.TestCase):
    def test_config_show_reports_key_status_without_printing_the_secret(self):
        output = StringIO()
        with patch.object(cli.settings_store, "load", return_value=default_settings()), patch.object(
            cli.settings_store,
            "get_api_key",
            return_value="synthetic-secret-value",
        ), patch.object(cli, "console", Console(file=output)):
            cli._show_settings()

        self.assertIn("configurada", output.getvalue())
        self.assertNotIn("synthetic-secret-value", output.getvalue())

    def test_config_flow_saves_cloud_ssh_profile_without_cloud_mcp_url(self):
        settings = default_settings()
        answers = [
            "ollama",
            settings["ollama_base_url"],
            settings["ollama_model"],
            settings["gemini_model"],
            settings["gemini_fallback_model"],
            "cloud",
            settings["mcp_urls"]["docker"],
            settings["mcp_urls"]["virtualbox"],
            "192.0.2.10",
            "kali",
            "C:\\keys\\kali.pem",
            "C:\\Users\\test\\.ssh\\known_hosts",
            "Max",
        ]
        with patch.object(cli.settings_store, "load", return_value=settings), patch.object(
            cli.settings_store, "save", side_effect=lambda saved: saved
        ) as save, patch.object(cli.Prompt, "ask", side_effect=answers), patch.object(
            cli.IntPrompt, "ask", side_effect=[settings["ollama_timeout"], settings["gemini_timeout"], 2222]
        ), patch.object(cli, "apply_runtime_settings") as apply:
            cli._configure_settings()

        saved = save.call_args.args[0]
        self.assertEqual(saved["kali_backend"], "cloud")
        self.assertEqual(saved["cloud_ssh"]["host"], "192.0.2.10")
        self.assertEqual(saved["cloud_ssh"]["port"], 2222)
        self.assertEqual(saved["cloud_ssh"]["key_path"], "C:\\keys\\kali.pem")
        self.assertEqual(saved["mcp_urls"]["cloud"], "")
        apply.assert_called_once_with(saved)

    def test_config_command_opens_settings_flow_instead_of_dispatching_as_chat(self):
        settings = default_settings()
        with patch.object(cli, "apply_runtime_settings", return_value=settings), patch.object(
            cli, "print_banner"
        ), patch.object(cli.Prompt, "ask", side_effect=["config", "exit"]), patch.object(
            cli, "_configure_settings"
        ) as configure, patch.object(cli.dispatcher, "process_input") as process_input:
            cli.main()

        configure.assert_called_once_with()
        process_input.assert_not_called()


if __name__ == "__main__":
    unittest.main()
