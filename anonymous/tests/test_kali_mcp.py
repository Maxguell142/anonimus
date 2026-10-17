import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        res = dispatcher.process_input("kali status")
        self.assertEqual(res["type"], "status")
        self.assertIn("Kali MCP", res["message"])

    def test_start_requires_hitl(self):
        res = dispatcher.process_input("kali start")
        self.assertEqual(res["type"], "confirmation_required")

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
        with patch.object(engine, "docker_available", return_value=False):
            res = engine.start_stack(confirmed=True)
        self.assertFalse(res["ok"])
        self.assertIn("Docker no está", res["message"])


if __name__ == "__main__":
    unittest.main()
