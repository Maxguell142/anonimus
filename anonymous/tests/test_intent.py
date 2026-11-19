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

    def test_vulnerability_ranking_question_routes_to_local_summary(self):
        for request in (
            "quiero que me digas cuales estan mas bulnerables",
            "qué equipos son más vulnerables",
        ):
            with self.subTest(request=request):
                intent = parse_intent(request)
                self.assertEqual(intent["action"], "vulnerability_summary")

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

    def test_network_scan_request_requires_cidr(self):
        intent = parse_intent("quiero que realisemmo un escaneo de la red")
        self.assertEqual(intent["action"], "kali_network_discovery")
        self.assertIsNone(intent["target"])

    def test_informal_analyze_my_network_request_routes_to_discovery(self):
        intent = parse_intent("analisa mi red")
        self.assertEqual(intent["action"], "kali_network_discovery")
        self.assertIsNone(intent["target"])
        self.assertTrue(intent["local_network"])

    def test_network_scan_with_cidr_routes_to_kali(self):
        intent = parse_intent("quiero escanear mi red 192.168.0.0/24")
        self.assertEqual(intent["action"], "kali_network_discovery")
        self.assertEqual(intent["target"], "192.168.0.0/24")

    def test_natural_kali_scan_request_routes_to_discovery(self):
        intent = parse_intent("hola quiero iniciar un escaneo con kali")
        self.assertEqual(intent["action"], "kali_network_discovery")
        self.assertIsNone(intent["target"])

    def test_scan_pronoun_does_not_become_a_host_target(self):
        intent = parse_intent("escanealo vos")
        self.assertEqual(intent["action"], "kali_network_discovery")
        self.assertIsNone(intent["target"])
        self.assertTrue(intent["local_network"])

    def test_kali_capabilities_question_uses_a_static_route(self):
        intent = parse_intent("pregunta, que podes hacer con kali?")
        self.assertEqual(intent["action"], "kali_capabilities")

    def test_vague_request_to_perform_something_in_kali_does_not_go_to_ai(self):
        intent = parse_intent("bueno quiero que lo realises en kali")
        self.assertEqual(intent["action"], "kali_capabilities")

    def test_vague_numbered_option_execution_does_not_go_to_ai(self):
        intent = parse_intent("vamos a relisar la segunda opccion")
        self.assertEqual(intent["action"], "kali_capabilities")

    def test_operational_attack_request_is_restricted_before_ai_fallback(self):
        intent = parse_intent("quiero inicies un taque")
        self.assertEqual(intent["action"], "kali_unsupported_operation")

    def test_vulnerability_scan_request_is_restricted_before_ai_fallback(self):
        intent = parse_intent("vamos a realizar un escaneo de vulnerabilidades con nmap")
        self.assertEqual(intent["action"], "kali_unsupported_operation")

    def test_unknown_device_question_routes_to_network_discovery(self):
        intent = parse_intent("mi misma red, quiero ver si hay algun dispositivo desconocido")
        self.assertEqual(intent["action"], "kali_network_discovery")
        self.assertIsNone(intent["target"])

    def test_connected_device_count_request_routes_to_network_discovery(self):
        intent = parse_intent("red, solo veremos cuantos equipos estan conectados")
        self.assertEqual(intent["action"], "kali_network_discovery")
        self.assertIsNone(intent["target"])

    def test_misspelled_connected_device_question_routes_to_network_discovery(self):
        intent = parse_intent(
            "quiero que me digas cuandots equipos estan conectasdos "
            "y cuales estan mas bulnerables"
        )
        self.assertEqual(intent["action"], "kali_network_discovery")
        self.assertIsNone(intent["target"])

    def test_network_analysis_request_with_connected_device_count_routes_to_discovery(self):
        intent = parse_intent(
            "quiero que analisis mi red y me digas cuantos equips hay conectados"
        )
        self.assertEqual(intent["action"], "kali_network_discovery")
        self.assertIsNone(intent["target"])
        self.assertTrue(intent["local_network"])

    def test_router_inventory_request_routes_to_local_network_discovery(self):
        for request in (
            "quiero analizar mi router y contar equipos conectados",
            "quiero revisar la seguridad de mi ruter",
            "de mi router",
        ):
            with self.subTest(request=request):
                intent = parse_intent(request)
                self.assertEqual(intent["action"], "kali_network_discovery")
                self.assertIsNone(intent["target"])
                self.assertTrue(intent["local_network"])

    def test_natural_kali_connection_requests_route_to_stack_start(self):
        for request in (
            "iniciemos conexion con kali",
            "inicia kali",
            "inisia kali",
            "quiero iniciar Kali",
            "conectemos con Kali Docker",
        ):
            with self.subTest(request=request):
                intent = parse_intent(request)
                self.assertEqual(intent["action"], "kali_start_stack")

    def test_conceptual_network_scan_question_stays_in_rag(self):
        intent = parse_intent("qué es un escaneo de red")
        self.assertEqual(intent["action"], "rag")

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
