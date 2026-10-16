import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.core.intent import parse_intent


class TestParseIntent(unittest.TestCase):
    def test_spanish_scan_localhost(self):
        intent = parse_intent("escaneá localhost")
        self.assertIsNotNone(intent)
        self.assertEqual(intent["action"], "scan")
        self.assertEqual(intent["target"], "localhost")
        self.assertIsNone(intent["ports"])

    def test_scan_with_ip_and_ports(self):
        intent = parse_intent("scan 192.168.1.10 ports 80,443")
        self.assertEqual(intent["action"], "scan")
        self.assertEqual(intent["target"], "192.168.1.10")
        self.assertEqual(intent["ports"], "80,443")

    def test_ping_alive(self):
        intent = parse_intent("está vivo 127.0.0.1?")
        self.assertEqual(intent["action"], "ping")
        self.assertEqual(intent["target"], "127.0.0.1")

    def test_rag_owasp(self):
        intent = parse_intent("qué dice OWASP sobre inyección SQL")
        self.assertEqual(intent["action"], "rag")
        self.assertIn("inyección", intent["query"].lower())

    def test_ptt_and_status_and_findings(self):
        self.assertEqual(parse_intent("mostrá el árbol de tareas")["action"], "ptt")
        self.assertEqual(parse_intent("estado del sistema")["action"], "status")
        self.assertEqual(parse_intent("mostrá los hallazgos")["action"], "findings")
        self.assertEqual(parse_intent("generá un reporte")["action"], "report")

    def test_conceptual_question_is_not_a_scan(self):
        intent = parse_intent("qué es un escaneo de puertos y cómo mitigarlo")
        self.assertIsNotNone(intent)
        self.assertEqual(intent["action"], "rag")

    def test_plain_chat_returns_none(self):
        self.assertIsNone(parse_intent("explicame cómo funciona TLS 1.3 en general"))

    def test_expanded_operational_phrases(self):
        self.assertEqual(parse_intent("mostrame el estado")["action"], "status")
        self.assertEqual(parse_intent("ver tareas pendientes")["action"], "ptt")
        self.assertEqual(parse_intent("borrá el árbol de tareas")["action"], "ptt_reset")
        self.assertEqual(parse_intent("listado de puertos abiertos")["action"], "findings")
        self.assertEqual(parse_intent("armá un informe")["action"], "report")

    def test_expanded_scan_and_ping_phrases(self):
        scan = parse_intent("revisá los puertos de localhost")
        self.assertEqual(scan["action"], "scan")
        self.assertEqual(scan["target"], "localhost")
        self.assertEqual(parse_intent("comprobá conectividad con 127.0.0.1")["action"], "ping")

    def test_defensive_questions_route_to_local_rag(self):
        for question in (
            "cómo proteger una API contra fuerza bruta",
            "qué controles usar para SSRF",
            "recomendaciones para gestionar parches",
        ):
            with self.subTest(question=question):
                intent = parse_intent(question)
                self.assertEqual(intent["action"], "rag")
                self.assertEqual(intent["query"], question)


if __name__ == "__main__":
    unittest.main()
