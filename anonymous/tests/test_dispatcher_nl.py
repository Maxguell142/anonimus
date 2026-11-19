import sys
import socket
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.core.dispatcher import Dispatcher, dispatcher
from anonymous.core.os_adapter import OSAdapter


class TestDispatcherNaturalLanguage(unittest.TestCase):
    def test_os_adapter_lists_active_private_ipv4_subnets_only(self):
        adapter = OSAdapter()
        addresses = {
            "Wi-Fi": [
                SimpleNamespace(
                    family=socket.AF_INET,
                    address="192.168.0.8",
                    netmask="255.255.255.0",
                )
            ],
            "vEthernet (WSL)": [
                SimpleNamespace(
                    family=socket.AF_INET,
                    address="172.21.32.1",
                    netmask="255.255.240.0",
                )
            ],
            "Public": [
                SimpleNamespace(
                    family=socket.AF_INET,
                    address="8.8.8.8",
                    netmask="255.255.255.0",
                )
            ],
            "Down": [
                SimpleNamespace(
                    family=socket.AF_INET,
                    address="10.0.0.2",
                    netmask="255.255.255.0",
                )
            ],
        }
        stats = {
            "Wi-Fi": SimpleNamespace(isup=True),
            "vEthernet (WSL)": SimpleNamespace(isup=True),
            "Public": SimpleNamespace(isup=True),
            "Down": SimpleNamespace(isup=False),
        }

        with patch("anonymous.core.os_adapter.psutil.net_if_addrs", return_value=addresses), patch(
            "anonymous.core.os_adapter.psutil.net_if_stats",
            return_value=stats,
        ):
            result = adapter.get_private_network_interfaces()

        self.assertEqual(
            result,
            [
                {
                    "name": "Wi-Fi",
                    "address": "192.168.0.8",
                    "netmask": "255.255.255.0",
                    "cidr": "192.168.0.0/24",
                },
                {
                    "name": "vEthernet (WSL)",
                    "address": "172.21.32.1",
                    "netmask": "255.255.240.0",
                    "cidr": "172.21.32.0/20",
                },
            ],
        )

    def test_owasp_question_goes_to_rag(self):
        res = dispatcher.process_input("qué dice OWASP sobre inyección SQL")
        self.assertEqual(res["type"], "rag")
        self.assertIn("OWASP", res["message"])

    def test_remote_scan_requires_hitl(self):
        res = dispatcher.process_input("escaneá 8.8.8.8")
        self.assertEqual(res["type"], "confirmation_required")
        self.assertTrue(res.get("pending_message"))

    def test_network_scan_without_cidr_asks_for_scope(self):
        res = dispatcher.process_input("quiero que realisemmo un escaneo de la red")
        self.assertEqual(res["type"], "chat")
        self.assertIn("CIDR", res["message"])

    def test_misspelled_connected_device_question_asks_for_scope_without_ai(self):
        agent = Dispatcher()
        question = (
            "quiero que me digas cuandots equipos estan conectasdos "
            "y cuales estan mas bulnerables"
        )
        with patch("anonymous.core.dispatcher.gemini_client.generate_response") as generate:
            result = agent.process_input(question)

        self.assertEqual(result["type"], "chat")
        self.assertIn("CIDR", result["message"])
        self.assertIn("no evalúa ni clasifica vulnerabilidades", result["message"])
        generate.assert_not_called()

    def test_network_analysis_with_connected_equips_uses_local_interface_lookup(self):
        agent = Dispatcher()
        interfaces = [
            {
                "name": "Wi-Fi",
                "address": "192.168.0.186",
                "netmask": "255.255.255.0",
                "cidr": "192.168.0.0/24",
            }
        ]
        with patch(
            "anonymous.core.dispatcher.os_adapter.get_private_network_interfaces",
            return_value=interfaces,
        ) as inspect_network, patch(
            "anonymous.core.dispatcher.gemini_client.generate_response"
        ) as generate:
            result = agent.process_input(
                "quiero que analisis mi red y me digas cuantos equips hay conectados"
            )

        inspect_network.assert_called_once_with()
        self.assertIn("Wi-Fi", result["message"])
        self.assertIn("192.168.0.0/24", result["message"])
        self.assertIn("elige", result["message"].lower())
        generate.assert_not_called()

    def test_router_inventory_request_detects_local_network_without_ai_or_scanning(self):
        agent = Dispatcher()
        interfaces = [
            {
                "name": "Wi-Fi",
                "address": "192.168.0.186",
                "netmask": "255.255.255.0",
                "cidr": "192.168.0.0/24",
            }
        ]
        with patch(
            "anonymous.core.dispatcher.os_adapter.get_private_network_interfaces",
            return_value=interfaces,
        ) as inspect_network, patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network"
        ) as discover, patch(
            "anonymous.core.dispatcher.gemini_client.generate_response"
        ) as generate:
            result = agent.process_input(
                "quiero analizar mi router y contar equipos conectados"
            )

        inspect_network.assert_called_once_with()
        self.assertIn("Wi-Fi", result["message"])
        self.assertIn("192.168.0.0/24", result["message"])
        discover.assert_not_called()
        generate.assert_not_called()

    def test_informal_analyze_my_network_request_detects_interfaces_without_ai(self):
        agent = Dispatcher()
        interfaces = [
            {
                "name": "Wi-Fi",
                "address": "192.168.0.186",
                "netmask": "255.255.255.0",
                "cidr": "192.168.0.0/24",
            }
        ]
        with patch(
            "anonymous.core.dispatcher.os_adapter.get_private_network_interfaces",
            return_value=interfaces,
        ) as inspect_network, patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network"
        ) as discover, patch(
            "anonymous.core.dispatcher.gemini_client.generate_response"
        ) as generate:
            result = agent.process_input("analisa mi red")

        inspect_network.assert_called_once_with()
        self.assertIn("Wi-Fi", result["message"])
        self.assertIn("192.168.0.0/24", result["message"])
        discover.assert_not_called()
        generate.assert_not_called()

    def test_vulnerability_question_explains_assessment_limit_without_scanning(self):
        agent = Dispatcher()
        with patch(
            "anonymous.core.dispatcher.ollama_client.answer_kali_question",
            return_value=None,
        ), patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network"
        ) as discover:
            result = agent.process_input(
                "quiero que todo lo analice Anonymous y me digas cuales estan mas vulnerables"
            )

        self.assertEqual(result["type"], "chat")
        self.assertIn("no puedo determinar", result["message"].lower())
        self.assertIn("no ejecutará comandos arbitrarios", result["message"].lower())
        self.assertIn("findings", result["message"])
        discover.assert_not_called()

    def test_vulnerability_question_without_scan_does_not_claim_assessment(self):
        agent = Dispatcher()
        with patch(
            "anonymous.core.dispatcher.ollama_client.answer_kali_question",
            return_value=None,
        ), patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network"
        ) as discover, patch(
            "anonymous.core.dispatcher.recon_engine.scan_ports"
        ) as scan_ports:
            result = agent.process_input(
                "quiero que me digas cuales estan mas bulnerables"
            )

        self.assertIn("no puedo determinar", result["message"].lower())
        self.assertIn("no identifica servicios", result["message"].lower())
        discover.assert_not_called()
        scan_ports.assert_not_called()

    def test_vulnerability_question_uses_ollama_with_last_kali_discovery_facts(self):
        agent = Dispatcher()
        facts = {
            "reported_up": 2,
            "confirmed_echo_replies": 2,
            "uncertain_tcp_resets": 0,
        }
        agent._last_discovery_context = {
            "target": "192.168.0.0/24",
            "facts": facts,
        }
        with patch(
            "anonymous.core.dispatcher.ollama_client.answer_kali_question",
            return_value="El descubrimiento no permite evaluar vulnerabilidades.",
        ) as answer_question:
            result = agent.process_input(
                "quiero que me digas cuales estan mas bulnerables"
            )

        answer_question.assert_called_once_with(
            "quiero que me digas cuales estan mas bulnerables",
            "192.168.0.0/24",
            facts,
        )
        self.assertIn("no permite evaluar", result["message"])

    def test_network_scan_with_cidr_requires_confirmation(self):
        res = dispatcher.process_input("quiero escanear mi red 192.168.0.0/24")
        self.assertEqual(res["type"], "confirmation_required")
        self.assertEqual(res["target"], "192.168.0.0/24")
        self.assertIn("kali discover", res["pending_message"])

    def test_natural_kali_start_requests_require_confirmation(self):
        agent = Dispatcher()
        for request in ("iniciemos conexion con kali", "inicia kali", "inisia kali"):
            with self.subTest(request=request), patch(
                "anonymous.core.dispatcher.kali_forensics_engine.start_container",
                return_value={
                    "type": "confirmation_required",
                    "message": "Confirmación requerida",
                },
            ) as start_container:
                result = agent.process_input(request)

            self.assertEqual(result["type"], "confirmation_required")
            self.assertIn("kali start", result["pending_message"])
            start_container.assert_called_once_with(False)

    def test_natural_kali_request_accepts_cidr_as_follow_up(self):
        agent = Dispatcher()
        prompt = agent.process_input("hola quiero iniciar un escaneo con kali")
        self.assertIn("CIDR", prompt["message"])

        confirmation = agent.process_input("192.168.0.0/24")
        self.assertEqual(confirmation["type"], "confirmation_required")
        self.assertEqual(confirmation["target"], "192.168.0.0/24")

    def test_scan_pronoun_followup_keeps_waiting_for_network_scope(self):
        agent = Dispatcher()
        with patch(
            "anonymous.core.dispatcher.os_adapter.get_private_network_interfaces",
            return_value=[],
        ), patch.object(agent, "_handle_scan") as scan, patch.object(
            agent, "_handle_ai_query"
        ) as ai_query:
            agent.process_input("escanea mi red")
            clarification = agent.process_input("con las herramientas de kali")
            response = agent.process_input("escanealo vos")

        self.assertIn("CIDR", clarification["message"])
        self.assertIn("CIDR", response["message"])
        scan.assert_not_called()
        ai_query.assert_not_called()

    def test_kali_capabilities_are_described_without_calling_ai(self):
        agent = Dispatcher()
        with patch.object(agent, "_handle_ai_query") as ai_query:
            responses = [
                agent.process_input(request)
                for request in (
                    "pregunta, que podes hacer con kali?",
                    "bueno quiero que lo realises en kali",
                    "vamos a relisar la segunda opccion",
                )
            ]

        for response in responses:
            self.assertIn("descubrimiento de hosts", response["message"].lower())
            self.assertIn("forense", response["message"].lower())
            self.assertIn("vulnerabilidades", response["message"].lower())
        ai_query.assert_not_called()

    def test_attack_request_is_refused_without_calling_ai(self):
        agent = Dispatcher()
        with patch.object(agent, "_handle_ai_query") as ai_query:
            responses = [
                agent.process_input(request)
                for request in (
                    "quiero inicies un taque",
                    "vamos a realizar un escaneo de vulnerabilidades con nmap",
                )
            ]

        for response in responses:
            self.assertIn("no puedo", response["message"].lower())
            self.assertIn("nmap -sn", response["message"].lower())
        ai_query.assert_not_called()

    def test_confirmation_without_cidr_keeps_scope_request_in_context(self):
        agent = Dispatcher()
        agent.process_input("quiero que realicemos un escaneo de la red")

        with patch.object(agent, "_handle_ai_query") as ai_query:
            response = agent.process_input("comfirmo")

        self.assertIn("CIDR", response["message"])
        ai_query.assert_not_called()

    def test_natural_scope_clarification_does_not_fall_back_to_ai(self):
        agent = Dispatcher()
        agent.process_input("quiero que realicemos un escaneo de la red")

        with patch.object(agent, "_handle_ai_query") as ai_query:
            response = agent.process_input("red, solo veremos cuantos equipos estan conectados")

        self.assertIn("CIDR", response["message"])
        ai_query.assert_not_called()

    def test_short_yes_while_waiting_for_cidr_does_not_fall_back_to_ai(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")

        with patch.object(agent, "_handle_ai_query") as ai_query:
            response = agent.process_input("s")

        self.assertIn("CIDR", response["message"])
        ai_query.assert_not_called()

    def test_user_asks_agent_to_find_own_network_and_selects_it_before_scan_confirmation(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")
        interfaces = [
            {
                "name": "Wi-Fi",
                "address": "192.168.0.8",
                "netmask": "255.255.255.0",
                "cidr": "192.168.0.0/24",
            }
        ]

        with patch(
            "anonymous.core.dispatcher.os_adapter.get_private_network_interfaces",
            return_value=interfaces,
        ) as inspect_network, patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            return_value={
                "type": "confirmation_required",
                "target": "192.168.0.0/24",
                "pending_message": "kali discover 192.168.0.0/24",
                "message": "Confirma autorización para 192.168.0.0/24",
            },
        ) as discover, patch.object(agent, "_handle_ai_query") as ai_query:
            offered = agent.process_input("quiero que lo realises vos")
            discover.assert_not_called()
            selected = agent.process_input("sí, esa red Wi-Fi")

        inspect_network.assert_called_once_with()
        self.assertIn("192.168.0.0/24", offered["message"])
        self.assertEqual(selected["type"], "confirmation_required")
        self.assertIn("192.168.0.0/24", selected["message"])
        discover.assert_called_once_with("192.168.0.0/24", False)
        ai_query.assert_not_called()

    def test_scan_of_my_network_starts_local_interface_lookup_without_manual_ipconfig(self):
        agent = Dispatcher()
        interfaces = [
            {
                "name": "Wi-Fi",
                "address": "192.168.0.8",
                "netmask": "255.255.255.0",
                "cidr": "192.168.0.0/24",
            }
        ]
        with patch(
            "anonymous.core.dispatcher.os_adapter.get_private_network_interfaces",
            return_value=interfaces,
        ) as inspect_network, patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network"
        ) as discover:
            result = agent.process_input(
                "quiero que realisemos un escaneo de mi coxion de red"
            )

        inspect_network.assert_called_once_with()
        self.assertIn("192.168.0.0/24", result["message"])
        self.assertIn("Wi-Fi", result["message"])
        discover.assert_not_called()

    def test_follow_up_to_inspect_current_network_detects_local_interfaces(self):
        interfaces = [
            {
                "name": "Wi-Fi",
                "address": "192.168.0.8",
                "netmask": "255.255.255.0",
                "cidr": "192.168.0.0/24",
            }
        ]
        for follow_up in ("mi red actual", "fijate vos", "identifica mi red"):
            with self.subTest(follow_up=follow_up):
                agent = Dispatcher()
                agent.process_input(
                    "quiero que me digas cuantos equipos estan conectados"
                )
                with patch(
                    "anonymous.core.dispatcher.os_adapter.get_private_network_interfaces",
                    return_value=interfaces,
                ) as inspect_network, patch(
                    "anonymous.core.dispatcher.kali_mcp_engine.discover_network"
                ) as discover:
                    result = agent.process_input(follow_up)

                inspect_network.assert_called_once_with()
                self.assertIn("192.168.0.0/24", result["message"])
                self.assertIn("elige", result["message"].lower())
                discover.assert_not_called()

    def test_automatic_network_detection_asks_which_interface_when_ambiguous(self):
        agent = Dispatcher()
        interfaces = [
            {"name": "Wi-Fi", "address": "192.168.0.8", "netmask": "255.255.255.0", "cidr": "192.168.0.0/24"},
            {"name": "Ethernet", "address": "10.0.0.8", "netmask": "255.255.255.0", "cidr": "10.0.0.0/24"},
        ]

        with patch(
            "anonymous.core.dispatcher.os_adapter.get_private_network_interfaces",
            return_value=interfaces,
        ), patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network"
        ) as discover:
            offered = agent.process_input("quiero escanear mi conexión de red")

        self.assertIn("Wi-Fi", offered["message"])
        self.assertIn("Ethernet", offered["message"])
        self.assertIn("elige", offered["message"].lower())
        discover.assert_not_called()

    def test_automatic_network_detection_with_no_candidates_reports_actual_limitation(self):
        agent = Dispatcher()
        with patch(
            "anonymous.core.dispatcher.os_adapter.get_private_network_interfaces",
            return_value=[],
        ), patch.object(agent, "_handle_ai_query") as ai_query:
            agent.process_input("quiero escanear mi red")
            result = agent.process_input("detecta la red vos")

        self.assertEqual(result["type"], "chat")
        self.assertIn("no encontr", result["message"].lower())
        ai_query.assert_not_called()

    def test_auto_detection_failure_is_reported_without_fallback_to_ai(self):
        agent = Dispatcher()
        with patch(
            "anonymous.core.dispatcher.os_adapter.get_private_network_interfaces",
            side_effect=OSError("no se pudo consultar interfaces"),
        ), patch.object(agent, "_handle_ai_query") as ai_query:
            agent.process_input("quiero escanear mi red")
            result = agent.process_input("encuentra mi red")

        self.assertIn("no se pudo consultar interfaces", result["message"])
        ai_query.assert_not_called()

    def test_ipv4_and_subnet_mask_require_adapter_clarification(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")

        with patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            return_value={"type": "confirmation_required", "target": "192.168.0.0/24"},
        ) as discover:
            result = agent.process_input(
                "IPv4 192.168.0.8, máscara de subred 255.255.255.0"
            )

        self.assertEqual(result["type"], "chat")
        self.assertIn("adaptador", result["message"].lower())
        self.assertIn("192.168.0.0/24", result["message"])
        discover.assert_not_called()

    def test_ipv4_only_requests_mask_without_falling_back_to_ai(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")

        with patch.object(agent, "_handle_ai_query") as ai_query:
            response = agent.process_input(
                "Dirección IPv4: 172.21.32.1"
            )

        self.assertIn("máscara", response["message"].lower())
        self.assertIn("172.21.32.1", response["message"])
        ai_query.assert_not_called()

    def test_subnet_mask_in_next_turn_uses_saved_ipv4(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")
        agent.process_input("Dirección IPv4: 172.21.32.1")

        with patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            return_value={"type": "confirmation_required", "target": "172.21.32.0/24"},
        ) as discover:
            result = agent.process_input("Máscara de subred: 255.255.255.0")

        self.assertEqual(result["type"], "chat")
        self.assertIn("adaptador", result["message"].lower())
        self.assertIn("172.21.32.0/24", result["message"])
        discover.assert_not_called()

    def test_adapter_must_be_explicitly_identified_before_confirmation(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")
        agent.process_input("Dirección IPv4: 172.21.32.1")
        agent.process_input("Máscara de subred: 255.255.255.0")

        with patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            return_value={"type": "confirmation_required", "target": "172.21.32.0/24"},
        ) as discover:
            ambiguous = agent.process_input("confirmo")
            selected = agent.process_input("es el adaptador Wi-Fi")

        self.assertIn("adaptador", ambiguous["message"].lower())
        discover.assert_called_once_with("172.21.32.0/24", False)
        self.assertEqual(selected["type"], "confirmation_required")
        self.assertEqual(selected["target"], "172.21.32.0/24")

    def test_virtual_adapter_name_requires_user_to_identify_intended_network(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")
        agent.process_input("Dirección IPv4: 172.21.32.1")
        agent.process_input("Máscara de subred: 255.255.255.0")

        with patch.object(agent, "_handle_ai_query") as ai_query, patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network"
        ) as discover:
            response = agent.process_input("vEthernet WSL")

        self.assertIn("WSL", response["message"])
        self.assertIn("Wi-Fi", response["message"])
        ai_query.assert_not_called()
        discover.assert_not_called()

    def test_ipv4_only_followed_by_mask_requires_adapter_then_hitl_before_discovery(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")
        agent.process_input("Dirección IPv4: 192.168.0.8")
        agent.process_input("Máscara de subred: 255.255.255.0")

        with patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            side_effect=[
                {
                    "type": "confirmation_required",
                    "target": "192.168.0.0/24",
                    "pending_message": "kali discover 192.168.0.0/24",
                },
                {"ok": True, "type": "kali_discovery", "message": "Discovery output"},
            ],
        ) as discover:
            result = agent.process_input("adaptador Wi-Fi")
            self.assertEqual(result["type"], "confirmation_required")
            self.assertEqual(result["target"], "192.168.0.0/24")

            completed = agent.confirm_pending_action(result)

        self.assertEqual(completed["type"], "kali_discovery")
        self.assertEqual(
            discover.call_args_list[0].args,
            ("192.168.0.0/24", False),
        )
        self.assertEqual(
            discover.call_args_list[1].args,
            ("192.168.0.0/24", True),
        )

    def test_confirm_pending_action_replays_pending_cidr_not_original_reply(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")
        with patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            side_effect=[
                {
                    "type": "confirmation_required",
                    "target": "192.168.0.0/24",
                    "pending_message": "kali discover 192.168.0.0/24",
                },
                {"ok": True, "type": "kali_discovery", "message": "Completed"},
            ],
        ) as discover, patch.object(agent, "_handle_ai_query") as ai_query:
            pending = agent.process_input("192.168.0.0/24")
            completed = agent.process_input(
                pending["pending_message"],
                confirmed_by_user=True,
            )

        self.assertEqual(pending["type"], "confirmation_required")
        self.assertEqual(completed["type"], "kali_discovery")
        self.assertEqual(discover.call_args_list[1].args, ("192.168.0.0/24", True))
        ai_query.assert_not_called()


    def test_unrelated_follow_up_does_not_abandon_pending_discovery(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")

        with patch.object(agent, "_handle_ai_query") as ai_query:
            response = agent.process_input("2")

        self.assertIn("CIDR", response["message"])
        ai_query.assert_not_called()

    def test_new_natural_request_with_cidr_replaces_pending_scope(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")

        with patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            return_value={"type": "confirmation_required", "target": "192.168.0.0/24"},
        ) as discover:
            response = agent.process_input("quiero escanear mi red 192.168.0.0/24")

        self.assertEqual(response["type"], "confirmation_required")
        self.assertEqual(response["target"], "192.168.0.0/24")
        discover.assert_called_once_with("192.168.0.0/24", False)

    def test_status_command_is_available_while_waiting_for_scope(self):
        agent = Dispatcher()
        agent.process_input("quiero iniciar un escaneo en kali")
        with patch(
            "anonymous.core.dispatcher.kali_mcp_engine.status",
            return_value={"available": True},
        ), patch(
            "anonymous.core.dispatcher.kali_mcp_engine.status_text",
            return_value="Kali status",
        ):
            response = agent.process_input("kali status")

        self.assertEqual(response["type"], "status")

    def test_provided_kali_scan_conversation_stays_on_discovery_until_confirmation(self):
        agent = Dispatcher()
        with patch.object(agent, "_handle_ai_query") as ai_query, patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            return_value={"type": "confirmation_required", "target": "172.21.32.0/24"},
        ) as discover:
            first = agent.process_input(
                "hola quiero que entremos kali para realisar un escaneo de la red"
            )
            confirmation_without_scope = agent.process_input("confirmo")
            address = agent.process_input("Dirección IPv4: 172.21.32.1")
            unrelated_number = agent.process_input("2")
            adapter = agent.process_input("Máscara de subred: 255.255.255.0")
            mask = agent.process_input("adaptador Wi-Fi")

        self.assertIn("CIDR", first["message"])
        self.assertIn("CIDR", confirmation_without_scope["message"])
        self.assertIn("172.21.32.1", address["message"])
        self.assertIn("CIDR", unrelated_number["message"])
        self.assertIn("172.21.32.0/24", adapter["message"])
        self.assertIn("adaptador", adapter["message"].lower())
        self.assertEqual(mask["type"], "confirmation_required")
        self.assertEqual(mask["target"], "172.21.32.0/24")
        discover.assert_called_once_with("172.21.32.0/24", False)
        ai_query.assert_not_called()

    def test_confirmed_discovery_is_interpreted_by_ai(self):
        agent = Dispatcher()
        tool_result = {
            "ok": True,
            "type": "kali_discovery",
            "target": "192.168.0.0/24",
            "output": "Nmap done: 256 IP addresses (256 hosts up) scanned in 4.05 seconds",
            "interpretation_facts": {
                "reported_up": 256,
                "confirmed_echo_replies": 7,
                "uncertain_tcp_resets": 249,
                "warning": "TCP reset may be generated by a gateway or intermediary.",
            },
            "message": "Raw scan result",
        }
        with patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            return_value=tool_result,
        ) as discover, patch(
            "anonymous.core.dispatcher.ollama_client.interpret_network_discovery",
            return_value="Solo 7 respuestas ICMP son evidencia de hosts.",
        ) as interpret:
            result = agent.process_input("kali discover 192.168.0.0/24", confirmed_by_user=True)

        self.assertEqual(result["type"], "kali_discovery")
        self.assertIn("Interpretación de Ollama", result["message"])
        self.assertIn("Solo 7 respuestas ICMP", result["message"])
        discover.assert_called_once_with("192.168.0.0/24", True)
        interpret.assert_called_once_with("192.168.0.0/24", tool_result["interpretation_facts"])

    def test_ai_interpretation_unavailable_uses_cautious_local_summary(self):
        agent = Dispatcher()
        tool_result = {
            "ok": True,
            "type": "kali_discovery",
            "target": "192.168.0.0/24",
            "output": "scan output",
            "interpretation_facts": {
                "reported_up": 256,
                "confirmed_echo_replies": 7,
                "uncertain_tcp_resets": 249,
                "warning": "TCP reset may be generated by a gateway or intermediary.",
            },
            "message": "Raw scan result",
        }
        with patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            return_value=tool_result,
        ), patch(
            "anonymous.core.dispatcher.ollama_client.interpret_network_discovery",
            return_value=None,
        ):
            result = agent.process_input("kali discover 192.168.0.0/24", confirmed_by_user=True)

        self.assertIn("Interpretación local", result["message"])
        self.assertIn("249", result["message"])
        self.assertIn("puerta de enlace", result["message"])

    def test_discovery_followup_interprets_echo_replies_without_gemini(self):
        agent = Dispatcher()
        facts = {
            "reported_up": 256,
            "confirmed_echo_replies": 7,
            "uncertain_tcp_resets": 249,
        }
        with patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            return_value={
                "ok": True,
                "type": "kali_discovery",
                "target": "192.168.0.0/24",
                "interpretation_facts": facts,
                "message": "Discovery completed",
            },
        ), patch(
            "anonymous.core.dispatcher.ollama_client.interpret_network_discovery",
            return_value=None,
        ), patch(
            "anonymous.core.dispatcher.ollama_client.answer_kali_question",
            return_value=None,
        ) as answer_question, patch.object(agent, "_handle_ai_query") as ai_query:
            completed = agent.process_input(
                "kali discover 192.168.0.0/24",
                confirmed_by_user=True,
            )
            answer = agent.process_input("entonces 7 son dispositivos?")

        self.assertEqual(completed["type"], "kali_discovery")
        self.assertEqual(answer["type"], "chat")
        self.assertIn("no necesariamente", answer["message"].lower())
        self.assertIn("7", answer["message"])
        self.assertIn("echo-reply", answer["message"])
        self.assertIn("no confirma", answer["message"].lower())
        answer_question.assert_called_once_with(
            "entonces 7 son dispositivos?",
            "192.168.0.0/24",
            facts,
        )
        ai_query.assert_not_called()

    def test_discovery_followup_does_not_claim_host_count_when_facts_are_missing(self):
        agent = Dispatcher()
        with patch(
            "anonymous.core.dispatcher.kali_mcp_engine.discover_network",
            return_value={
                "ok": True,
                "type": "kali_discovery",
                "target": "192.168.0.0/24",
                "interpretation_facts": {},
                "message": "Discovery completed",
            },
        ), patch(
            "anonymous.core.dispatcher.ollama_client.interpret_network_discovery",
            return_value=None,
        ), patch.object(agent, "_handle_ai_query") as ai_query:
            agent.process_input("kali discover 192.168.0.0/24", confirmed_by_user=True)
            answer = agent.process_input("entonces cuántos dispositivos hay?")

        self.assertIn("no tengo datos", answer["message"].lower())
        self.assertNotIn("256 hosts", answer["message"].lower())
        ai_query.assert_not_called()

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
