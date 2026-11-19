import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from subprocess import CompletedProcess

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.core.dispatcher import dispatcher
from anonymous.core.intent import parse_intent
from anonymous.engines.ops.kali_mcp import KaliMcpEngine


class TestKaliIntents(unittest.TestCase):
    def test_status_phrase(self):
        self.assertEqual(parse_intent("estado de kali")["action"], "kali_status")

    def test_start_stack_phrase(self):
        self.assertEqual(parse_intent("levantá kali")["action"], "kali_start_stack")

    def test_knowledge_phrase(self):
        self.assertEqual(parse_intent("playbook ssh")["action"], "kali_knowledge")

    def test_audit_is_routed_not_executed_as_scan(self):
        self.assertEqual(parse_intent("kali-audit")["action"], "kali_audit")


class TestKaliDispatcher(unittest.TestCase):
    def test_status_command(self):
        with patch(
            "anonymous.core.dispatcher.kali_forensics_engine.status",
            return_value={
                "connected": True,
                "container": "kali-forensics",
                "state": "running",
                "detail": "ready",
            },
        ), patch(
            "anonymous.core.dispatcher.kali_mcp_engine.mcp_health",
            return_value={"healthy": False, "detail": "connection refused"},
        ):
            res = dispatcher.process_input("kali status")
        self.assertEqual(res["type"], "status")
        self.assertIn("Contenedor: kali-forensics (running)", res["message"])
        self.assertIn("MCP opcional", res["message"])

    def test_start_requires_hitl(self):
        res = dispatcher.process_input("kali start")
        self.assertEqual(res["type"], "confirmation_required")

    def test_forensic_tools_are_available_in_dispatcher(self):
        res = dispatcher.process_input("kali forensic tools")
        self.assertEqual(res["type"], "kali_forensics")
        self.assertIn("metadata", res["message"])
        self.assertIn("ewf-verify", res["message"])
        self.assertIn("solo lectura", res["message"])

    def test_arbitrary_forensic_command_is_not_forwarded(self):
        res = dispatcher.process_input("kali forensic shell whoami")
        self.assertEqual(res["type"], "chat")
        self.assertIn("kali forensic tools", res["message"])

    def test_network_discovery_command_preserves_cidr(self):
        res = dispatcher.process_input("kali discover 192.168.0.0/24")
        self.assertEqual(res["type"], "confirmation_required")
        self.assertEqual(res["target"], "192.168.0.0/24")

    def test_audit_is_refused(self):
        res = dispatcher.process_input("kali-audit 10.0.0.1")
        self.assertIn("no copia ese bucle", res["message"])

    def test_exec_hydra_blocked(self):
        res = dispatcher.process_input("kali exec hydra -L users -P pass ssh://127.0.0.1")
        self.assertIn("Bloqueado", res["message"])

    def test_knowledge_search_finds_copied_docs(self):
        res = dispatcher.process_input("kali knowledge nmap")
        self.assertIn("nmap", res["message"].lower())


class TestKaliEngineSession(unittest.TestCase):
    def test_passive_session_and_finish(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = KaliMcpEngine()
            engine.sessions_dir = Path(tmp)
            started = engine.start_session("127.0.0.1", scope="passive")
            self.assertTrue(started["ok"])
            finished = engine.finish_session()
            self.assertTrue(finished["ok"])

    def test_full_scope_rejected(self):
        engine = KaliMcpEngine()
        res = engine.start_session("127.0.0.1", scope="full")
        self.assertFalse(res["ok"])

    def test_start_stack_without_docker(self):
        engine = KaliMcpEngine()
        with patch.object(engine, "_docker_executable", return_value=None):
            res = engine.start_stack(confirmed=True)
        self.assertFalse(res["ok"])
        self.assertIn("Docker no está", res["message"])

    def test_start_stack_reports_when_docker_desktop_daemon_is_not_ready(self):
        engine = KaliMcpEngine()
        with tempfile.TemporaryDirectory() as tmp:
            engine.compose = Path(tmp) / "compose.yml"
            engine.compose.write_text("services: {}", encoding="utf-8")
            with patch.object(engine, "_docker_executable", return_value="docker.exe"), patch.object(
                engine,
                "_ensure_docker_daemon",
                return_value="Abre Docker Desktop y vuelve a intentar `kali start`.",
            ), patch("anonymous.engines.ops.kali_mcp.subprocess.run") as run:
                result = engine.start_stack(confirmed=True)

        self.assertFalse(result["ok"])
        self.assertIn("Docker Desktop", result["message"])
        run.assert_not_called()

    def test_ensure_docker_daemon_opens_desktop_and_waits_for_engine(self):
        engine = KaliMcpEngine()
        with patch.object(engine, "_docker_desktop_executable", return_value="Docker Desktop.exe"), patch(
            "anonymous.engines.ops.kali_mcp.subprocess.run",
            side_effect=[
                CompletedProcess(args=["docker.exe", "info"], returncode=1, stdout="", stderr="not ready"),
                CompletedProcess(args=["docker.exe", "info"], returncode=0, stdout="ready", stderr=""),
            ],
        ) as run, patch("anonymous.engines.ops.kali_mcp.subprocess.Popen") as popen:
            error = engine._ensure_docker_daemon("docker.exe", timeout=1, poll_interval=0)

        self.assertIsNone(error)
        popen.assert_called_once()
        self.assertEqual(run.call_count, 2)

    def test_start_stack_runs_existing_compose_only_after_confirmation(self):
        engine = KaliMcpEngine()
        with tempfile.TemporaryDirectory() as tmp:
            compose = Path(tmp) / "compose.yml"
            compose.write_text("services: {}", encoding="utf-8")
            engine.compose = compose
            with patch.object(engine, "_docker_executable", return_value="docker.exe"), patch.object(
                engine, "_ensure_docker_daemon", return_value=None
            ), patch(
                "anonymous.engines.ops.kali_mcp.subprocess.run",
                return_value=CompletedProcess(
                    args=["docker.exe"], returncode=0, stdout="started", stderr=""
                ),
            ) as run, patch.object(
                engine,
                "mcp_health",
                return_value={"healthy": True, "detail": "MCP active"},
            ):
                pending = engine.start_stack()
                self.assertEqual(pending["type"], "confirmation_required")
                run.assert_not_called()

                started = engine.start_stack(confirmed=True)

        self.assertTrue(started["ok"])
        self.assertEqual(
            run.call_args.args[0],
            [
                "docker.exe",
                "compose",
                "-f",
                str(compose),
                "up",
                "-d",
            ],
        )

    def test_start_stack_reports_compose_error_instead_of_success(self):
        engine = KaliMcpEngine()
        with tempfile.TemporaryDirectory() as tmp:
            compose = Path(tmp) / "compose.yml"
            compose.write_text("services: {}", encoding="utf-8")
            engine.compose = compose
            with patch.object(engine, "_docker_executable", return_value="docker.exe"), patch.object(
                engine, "_ensure_docker_daemon", return_value=None
            ), patch(
                "anonymous.engines.ops.kali_mcp.subprocess.run",
                return_value=CompletedProcess(
                    args=["docker.exe"], returncode=1, stdout="", stderr="daemon unavailable"
                ),
            ):
                result = engine.start_stack(confirmed=True)

        self.assertFalse(result["ok"])
        self.assertIn("daemon unavailable", result["message"])


class TestKaliNetworkDiscovery(unittest.TestCase):
    def test_discovery_requires_confirmation_before_mcp_calls(self):
        engine = KaliMcpEngine()
        with patch.object(engine, "_mcp_request") as mcp_request:
            result = engine.discover_network("192.168.0.0/24")

        self.assertEqual(result["type"], "confirmation_required")
        self.assertEqual(result["target"], "192.168.0.0/24")
        mcp_request.assert_not_called()

    def test_discovery_calls_only_fixed_host_discovery_command(self):
        engine = KaliMcpEngine()
        replies = [
            ({}, None),
            ({}, None),
            ({"tools": [{"name": "execute_command"}]}, None),
            ({"content": [{"type": "text", "text": "Nmap done"}], "isError": False}, None),
        ]
        with patch.object(engine, "_mcp_request", side_effect=replies) as mcp_request:
            result = engine.discover_network("192.168.0.0/24", confirmed=True)

        self.assertTrue(result["ok"])
        self.assertIn("Nmap done", result["message"])
        self.assertEqual(mcp_request.call_args.args[0]["method"], "tools/call")
        self.assertEqual(
            mcp_request.call_args.args[0]["params"],
            {
                "name": "execute_command",
                "arguments": {"command": "nmap -sn -n --reason 192.168.0.0/24"},
            },
        )

    def test_discovery_displays_structured_command_output(self):
        engine = KaliMcpEngine()
        replies = [
            ({}, None),
            ({}, None),
            ({"tools": [{"name": "execute_command"}]}, None),
            (
                {
                    "content": [{"type": "text", "text": "ignored wrapper text"}],
                    "structuredContent": {
                        "result": {"stdout": "Host 192.168.0.1 is up", "stderr": "", "success": True}
                    },
                    "isError": False,
                },
                None,
            ),
        ]
        with patch.object(engine, "_mcp_request", side_effect=replies):
            result = engine.discover_network("192.168.0.0/24", confirmed=True)

        self.assertTrue(result["ok"])
        self.assertIn("Host 192.168.0.1 is up", result["output"])
        self.assertNotIn("ignored wrapper text", result["output"])

    def test_discovery_builds_cautious_interpretation_facts(self):
        engine = KaliMcpEngine()
        output = "\n".join(
            [
                f"Nmap scan report for 192.168.0.{index}\n"
                "Host is up, received echo-reply ttl 63 (0.017s latency)."
                for index in range(1, 8)
            ]
            + [
                f"Nmap scan report for 10.0.0.{index}\n"
                "Host is up, received reset ttl 63 (0.010s latency)."
                for index in range(1, 250)
            ]
            + ["Nmap done: 256 IP addresses (256 hosts up) scanned in 4.05 seconds"]
        )
        facts = engine._interpret_discovery_output(output)

        self.assertEqual(facts["reported_up"], 256)
        self.assertEqual(facts["confirmed_echo_replies"], 7)
        self.assertEqual(facts["uncertain_tcp_resets"], 249)
        self.assertIn("puerta de enlace", facts["warning"].lower())

    def test_discovery_rejects_public_or_broad_networks(self):
        engine = KaliMcpEngine()
        for target in ("8.8.8.0/24", "192.168.0.0/16"):
            with self.subTest(target=target), patch.object(engine, "_mcp_request") as mcp_request:
                result = engine.discover_network(target, confirmed=True)
                self.assertFalse(result["ok"])
                mcp_request.assert_not_called()

    def test_discovery_rejects_missing_or_invalid_cidr(self):
        engine = KaliMcpEngine()
        for target in ("", "192.168.0.0", "192.168.0.0/33"):
            with self.subTest(target=target), patch.object(engine, "_mcp_request") as mcp_request:
                result = engine.discover_network(target, confirmed=True)
                self.assertFalse(result["ok"])
                mcp_request.assert_not_called()

    def test_mcp_request_parses_streamable_http_event(self):
        engine = KaliMcpEngine()
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers.get.return_value = "test-session"
        response.read.return_value = (
            b'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"tools":[]}}\n\n'
        )
        with patch("urllib.request.urlopen", return_value=response):
            result, session_id = engine._mcp_request(
                {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            )

        self.assertEqual(result, {"tools": []})
        self.assertEqual(session_id, "test-session")

    def test_mcp_request_preserves_escaped_newlines_inside_sse_json(self):
        engine = KaliMcpEngine()
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers.get.return_value = None
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"instructions": "First paragraph.\n\nSecond paragraph."},
        }
        response.read.return_value = (
            f"event: message\ndata: {json.dumps(message)}\n\n".encode("utf-8")
        )
        with patch("urllib.request.urlopen", return_value=response):
            result, _session_id = engine._mcp_request(
                {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
            )

        self.assertEqual(
            result["instructions"],
            "First paragraph.\n\nSecond paragraph.",
        )

    def test_mcp_request_parses_gateway_escaped_event_terminator(self):
        engine = KaliMcpEngine()
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers.get.return_value = None
        response.read.return_value = (
            b'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"tools":[]}}\\n\\n'
        )
        with patch("urllib.request.urlopen", return_value=response):
            result, _session_id = engine._mcp_request(
                {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            )

        self.assertEqual(result, {"tools": []})

    def test_mcp_request_parses_data_only_event_stream_response(self):
        engine = KaliMcpEngine()
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers.get.return_value = "test-session"
        response.read.return_value = (
            b'data: {"jsonrpc":"2.0","id":2,"result":{"tools":[]}}\n\n'
        )
        with patch("urllib.request.urlopen", return_value=response):
            result, session_id = engine._mcp_request(
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
            )

        self.assertEqual(result, {"tools": []})
        self.assertEqual(session_id, "test-session")

    def test_mcp_request_reports_unexpected_non_json_response(self):
        engine = KaliMcpEngine()
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers.get.return_value = None
        response.read.return_value = b"upstream gateway unavailable"
        with patch("urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "respuesta MCP no válida.*upstream"):
                engine._mcp_request(
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
                )

    def test_docker_fallback_finds_per_user_install(self):
        engine = KaliMcpEngine()
        with tempfile.TemporaryDirectory() as temp_dir:
            docker = Path(temp_dir) / "Programs" / "DockerDesktop" / "resources" / "bin" / "docker.exe"
            docker.parent.mkdir(parents=True)
            docker.touch()
            with patch.dict("os.environ", {"LOCALAPPDATA": temp_dir}), patch(
                "shutil.which", return_value=None
            ), patch("anonymous.engines.ops.kali_mcp.os.name", "nt"):
                self.assertTrue(engine.docker_available())


if __name__ == "__main__":
    unittest.main()
