import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.brain.gemini_client import GeminiClient
from anonymous.engines.ops.kali_mcp import KaliMcpEngine
from anonymous.settings import apply_runtime_settings, default_settings


class TestSettingsRuntime(unittest.TestCase):
    def test_ai_client_can_switch_provider_without_recreating_dispatcher(self):
        client = GeminiClient(api_key="", provider="ollama")

        client.configure(
            provider="google",
            api_key="synthetic-key",
            model="gemini-test",
            fallback_model="gemini-fallback-test",
            timeout=9,
            ollama_base_url="http://127.0.0.1:11434",
            ollama_model="test-model",
            ollama_timeout=15,
        )

        self.assertEqual(client.provider, "google")
        self.assertEqual(client.api_key, "synthetic-key")
        self.assertEqual(client.model, "gemini-test")
        self.assertEqual(client.timeout, 9)

    def test_cloud_backend_uses_ssh_profile_instead_of_mcp_url(self):
        engine = KaliMcpEngine.__new__(KaliMcpEngine)
        engine.configure_backend(
            "cloud",
            {
                "docker": "http://127.0.0.1:666/mcp",
                "cloud": "https://kali.example/mcp",
                "virtualbox": "",
            },
            {
                "host": "kali.example",
                "username": "kali",
                "port": 22,
                "key_path": "C:\\keys\\kali.pem",
                "known_hosts": "C:\\Users\\test\\.ssh\\known_hosts",
            },
        )

        self.assertEqual(engine.backend, "cloud")
        self.assertEqual(engine.mcp_url, "")
        self.assertEqual(engine.ssh_transport.connection["host"], "kali.example")

    def test_unconfigured_remote_backend_does_not_probe_docker_endpoint(self):
        engine = KaliMcpEngine.__new__(KaliMcpEngine)
        engine.configure_backend(
            "virtualbox",
            {
                "docker": "http://127.0.0.1:666/mcp",
                "cloud": "",
                "virtualbox": "",
            },
        )

        self.assertFalse(engine.mcp_health()["healthy"])
        self.assertEqual(engine.mcp_url, "")

    def test_cloud_start_checks_ssh_without_starting_local_docker(self):
        engine = KaliMcpEngine.__new__(KaliMcpEngine)
        engine.configure_backend(
            "cloud",
            {
                "docker": "http://127.0.0.1:666/mcp",
                "cloud": "https://kali.example/mcp",
                "virtualbox": "",
            },
            {
                "host": "kali.example",
                "username": "kali",
                "port": 22,
                "key_path": "C:\\keys\\kali.pem",
                "known_hosts": "C:\\Users\\test\\.ssh\\known_hosts",
            },
        )

        with patch.object(
            engine.ssh_transport,
            "health_check",
            return_value={"healthy": True, "detail": "ok"},
        ), patch.object(engine, "_docker_executable") as docker:
            result = engine.start_stack(confirmed=True)

        self.assertTrue(result["ok"])
        docker.assert_not_called()

    def test_cloud_discovery_requires_confirmation_before_ssh(self):
        engine = KaliMcpEngine.__new__(KaliMcpEngine)
        engine.configure_backend(
            "cloud",
            {"docker": "", "cloud": "", "virtualbox": ""},
            {
                "host": "kali.example",
                "username": "kali",
                "port": 22,
                "key_path": "C:\\keys\\kali.pem",
                "known_hosts": "C:\\Users\\test\\.ssh\\known_hosts",
            },
        )

        with patch.object(engine.ssh_transport, "discover_network") as discover:
            result = engine.discover_network("192.168.0.0/24")

        self.assertEqual(result["type"], "confirmation_required")
        self.assertEqual(result["target"], "192.168.0.0/24")
        self.assertIn("por SSH", result["message"])
        discover.assert_not_called()

    def test_cloud_stop_never_stops_the_local_docker_stack(self):
        engine = KaliMcpEngine.__new__(KaliMcpEngine)
        engine.configure_backend(
            "cloud",
            {
                "docker": "http://127.0.0.1:666/mcp",
                "cloud": "https://kali.example/mcp",
                "virtualbox": "",
            },
            {
                "host": "kali.example",
                "username": "kali",
                "port": 22,
                "key_path": "C:\\keys\\kali.pem",
                "known_hosts": "C:\\Users\\test\\.ssh\\known_hosts",
            },
        )

        with patch.object(engine, "_docker_executable") as docker:
            result = engine.stop_stack(confirmed=True)

        self.assertFalse(result["ok"])
        self.assertIn("no se ejecutó", result["message"])
        docker.assert_not_called()

    def test_confirmed_cloud_discovery_routes_the_fixed_command_through_ssh(self):
        engine = KaliMcpEngine.__new__(KaliMcpEngine)
        with tempfile.TemporaryDirectory() as temp_dir:
            key_path = Path(temp_dir) / "kali.pem"
            known_hosts = Path(temp_dir) / "known_hosts"
            key_path.touch()
            known_hosts.touch()
            engine.configure_backend(
                "cloud",
                {
                    "docker": "http://127.0.0.1:666/mcp",
                    "cloud": "https://kali.example/mcp",
                    "virtualbox": "",
                },
                {
                    "host": "192.0.2.10",
                    "username": "kali",
                    "port": 22,
                    "key_path": str(key_path),
                    "known_hosts": str(known_hosts),
                },
            )
            completed = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="Nmap done: 2 IP addresses (1 host up)",
                stderr="",
            )
            with patch.object(engine, "_save_discovery_output", return_value=None), patch(
                "anonymous.engines.ops.kali_ssh.shutil.which",
                return_value="ssh.exe",
            ), patch(
                "anonymous.engines.ops.kali_ssh.subprocess.run",
                return_value=completed,
            ) as run:
                result = engine.discover_network("192.168.0.0/24", confirmed=True)

            command = run.call_args.args[0]
            self.assertTrue(result["ok"])
            self.assertEqual(command[-2], "kali@192.0.2.10")
            self.assertEqual(
                command[-1],
                "nmap -sn -n --reason 192.168.0.0/24",
            )

    def test_runtime_settings_apply_to_existing_clients_and_keep_provider_key_scoped(self):
        settings = default_settings()
        settings.update(ai_provider="google", kali_backend="cloud")
        settings["mcp_urls"]["cloud"] = "https://kali.example/mcp"

        with patch("anonymous.brain.gemini_client.gemini_client") as ai_client, patch(
            "anonymous.brain.gemini_client.ollama_client"
        ) as ollama_client, patch("anonymous.engines.ops.kali_mcp.kali_mcp_engine") as kali_engine, patch(
            "anonymous.settings.settings_store.get_api_key",
            return_value="synthetic-key",
        ):
            apply_runtime_settings(settings)

        self.assertEqual(ai_client.configure.call_args.kwargs["provider"], "google")
        self.assertEqual(ai_client.configure.call_args.kwargs["api_key"], "synthetic-key")
        self.assertEqual(ollama_client.configure.call_args.kwargs["provider"], "ollama")
        self.assertEqual(ollama_client.configure.call_args.kwargs["api_key"], "")
        self.assertEqual(
            ollama_client.configure.call_args.kwargs["ollama_base_url"],
            settings["ollama_base_url"],
        )
        kali_engine.configure_backend.assert_called_once_with(
            "cloud",
            settings["mcp_urls"],
            settings["cloud_ssh"],
        )

    def test_ollama_runtime_does_not_read_or_forward_gemini_key(self):
        settings = default_settings()
        with patch("anonymous.brain.gemini_client.gemini_client") as ai_client, patch(
            "anonymous.brain.gemini_client.ollama_client"
        ) as ollama_client, patch("anonymous.engines.ops.kali_mcp.kali_mcp_engine"), patch(
            "anonymous.settings.settings_store.get_api_key"
        ) as get_api_key:
            apply_runtime_settings(settings)

        get_api_key.assert_not_called()
        self.assertEqual(ai_client.configure.call_args.kwargs["api_key"], "")
        self.assertEqual(ollama_client.configure.call_args.kwargs["api_key"], "")


if __name__ == "__main__":
    unittest.main()
