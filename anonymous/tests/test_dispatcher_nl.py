import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.core.dispatcher import dispatcher


class TestDispatcherNaturalLanguage(unittest.TestCase):
    def test_owasp_question_goes_to_rag(self):
        res = dispatcher.process_input("qué dice OWASP sobre inyección SQL")
        self.assertEqual(res["type"], "rag")
        self.assertIn("OWASP", res["message"])

    def test_remote_scan_requires_hitl(self):
        res = dispatcher.process_input("escaneá 8.8.8.8")
        self.assertEqual(res["type"], "confirmation_required")
        self.assertTrue(res.get("pending_message"))

    def test_status_phrase(self):
        res = dispatcher.process_input("estado del sistema")
        self.assertEqual(res["type"], "status")

    def test_remote_ping_requires_hitl(self):
        res = dispatcher.process_input("está vivo 8.8.8.8")
        self.assertEqual(res["type"], "confirmation_required")
        self.assertIn("ping", res.get("pending_message", ""))

    def test_local_ping_does_not_require_hitl(self):
        res = dispatcher.process_input("ping 127.0.0.1")
        self.assertEqual(res["type"], "ping")

    def test_unrecognized_text_reaches_ai_unchanged(self):
        with patch("anonymous.core.dispatcher.session_manager.save_message"), patch(
            "anonymous.core.dispatcher.session_manager.get_recent_messages",
            return_value=[],
        ), patch(
            "anonymous.core.dispatcher.gemini_client.generate_response",
            return_value="respuesta",
        ) as generate_response:
            res = dispatcher.process_input("lsholahola")

        self.assertEqual(res["type"], "chat")
        self.assertEqual(generate_response.call_args.kwargs["prompt"], "lsholahola")


if __name__ == "__main__":
    unittest.main()
