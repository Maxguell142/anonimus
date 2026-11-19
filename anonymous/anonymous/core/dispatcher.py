"""
Core Request Dispatcher for Anonymous.
Coordinates AgentShield guardrails, Gemini brain, Red/Blue engines, and Session persistence.
"""

import ipaddress
import re
from typing import Dict, Any, List, Optional
from anonymous.core.session import session_manager
from anonymous.core.intent import parse_intent
from anonymous.core.os_adapter import os_adapter
from anonymous.guardrails.agent_shield import agent_shield
from anonymous.guardrails.context_budget import context_budget
from anonymous.brain.gemini_client import gemini_client, ollama_client
from anonymous.brain.prompts import SYSTEM_PROMPT, RED_TEAM_PROMPT, BLUE_TEAM_PROMPT
from anonymous.engines.red.recon import recon_engine
from anonymous.engines.red.ptt import ptt_engine, TaskStatus
from anonymous.engines.blue.rag_engine import rag_engine
from anonymous.engines.ops.briefing import briefing_engine
from anonymous.engines.ops.kali_mcp import kali_mcp_engine
from anonymous.engines.ops.kali_forensics import kali_forensics_engine


class Dispatcher:
    """Central orchestrator for Anonymous requests."""

    def __init__(self) -> None:
        self._awaiting_network_cidr = False
        self._pending_network_address: Optional[str] = None
        self._awaiting_network_adapter = False
        self._pending_network_cidr: Optional[str] = None
        self._awaiting_network_selection = False
        self._pending_network_candidates: List[Dict[str, str]] = []
        self._last_discovery_context: Optional[Dict[str, Any]] = None

    def process_input(self, user_text: str, confirmed_by_user: bool = False) -> Dict[str, Any]:
        text = user_text.strip()
        if not text:
            return {"type": "empty", "message": "Por favor escribe un comando o consulta."}

        if self._awaiting_network_selection:
            return self._handle_network_selection(text, confirmed_by_user)

        if self._awaiting_network_adapter:
            explicit_cidr = self._network_cidr_from_input(text)
            if explicit_cidr and "/" in text:
                self._clear_pending_network()
                return self._handle_kali_network_discovery(explicit_cidr, confirmed_by_user)
            if self._is_local_network_request(text):
                return self._detect_local_networks()
            new_intent = parse_intent(text)
            if new_intent and new_intent.get("action") == "kali_network_discovery":
                self._clear_pending_network()
                target = new_intent.get("target")
                if target:
                    return self._handle_kali_network_discovery(target, confirmed_by_user)
                self._awaiting_network_cidr = True
                return self._network_cidr_prompt()
            if new_intent and new_intent.get("action") != "kali_network_discovery":
                self._clear_pending_network()
            else:
                return self._handle_network_adapter_answer(text)

        if self._awaiting_network_cidr:
            cidr = self._network_cidr_from_input(text)
            if cidr and "/" in text:
                self._awaiting_network_cidr = False
                self._pending_network_address = None
                return self._handle_kali_network_discovery(cidr, confirmed_by_user)
            if self._is_local_network_request(text):
                return self._detect_local_networks()
            if cidr:
                self._awaiting_network_cidr = False
                self._pending_network_address = None
                return self._request_network_adapter(cidr)
            if self._is_confirmation(text):
                return self._network_cidr_prompt()
            address = self._single_ipv4_from_input(text)
            if address:
                if self._pending_network_address:
                    try:
                        network = ipaddress.IPv4Interface(
                            f"{self._pending_network_address}/{address}"
                        ).network
                    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
                        return self._network_mask_prompt(self._pending_network_address)
                    self._awaiting_network_cidr = False
                    self._pending_network_address = None
                    return self._request_network_adapter(str(network))
                self._pending_network_address = address
                return self._network_mask_prompt(address)
            if text.isdecimal() or re.fullmatch(r"[\d.]+", text):
                return self._network_cidr_prompt()
            pending_intent = parse_intent(text)
            if pending_intent and pending_intent.get("action") == "kali_network_discovery":
                return self._network_cidr_prompt()
            if pending_intent or text.split()[0].lower() in {
                "help", "ayuda", "?", "comandos", "status", "estado", "briefing",
                "ptt", "findings", "hallazgos", "ping", "report", "reporte", "scan",
                "escanear", "rag", "normativa", "kali", "kali-start", "kali-audit",
                "kali-finish", "kalistart",
            }:
                self._awaiting_network_cidr = False
                self._pending_network_address = None
            else:
                return self._network_cidr_prompt()

        if self._last_discovery_context and self._is_discovery_followup(text):
            return self._answer_discovery_followup(self._last_discovery_context, text)

        parts = text.split()
        cmd = parts[0].lower()

        if cmd in ("help", "ayuda", "?", "comandos"):
            return self._handle_help()
        if cmd in ("status", "estado", "briefing"):
            return self._handle_status()
        if cmd == "ptt":
            sub = parts[1].lower() if len(parts) > 1 else ""
            if sub == "reset":
                ptt_engine.reset_tree()
                return {"type": "ptt_reset", "message": "Árbol de tareas PTT reiniciado a estado inicial."}
            return self._handle_ptt()
        if cmd in ("findings", "hallazgos"):
            return self._handle_findings()
        if cmd == "ping":
            target = parts[1] if len(parts) > 1 else "127.0.0.1"
            return self._handle_ping(target, confirmed_by_user)
        if cmd in ("report", "reporte"):
            return self._handle_report()
        if cmd in ("scan", "escanear"):
            target = parts[1] if len(parts) > 1 else "127.0.0.1"
            if "/" in target:
                return self._handle_kali_network_discovery(target, confirmed_by_user)
            ports_arg = parts[2] if len(parts) > 2 else None
            return self._handle_scan(target, ports_arg, confirmed_by_user)
        if cmd in ("rag", "normativa"):
            query = " ".join(parts[1:]) if len(parts) > 1 else "seguridad"
            return self._handle_rag(query)
        if cmd in ("kali", "kali-start", "kali-audit", "kali-finish", "kalistart"):
            return self._handle_kali(text, confirmed_by_user)

        intent = parse_intent(text)
        if intent:
            return self._dispatch_intent(intent, confirmed_by_user)

        return self._handle_ai_query(text)

    def confirm_pending_action(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Replay the action represented by a confirmation result, not its user's last reply."""
        pending_message = result.get("pending_message")
        if not isinstance(pending_message, str) or not pending_message.strip():
            return {
                "type": "chat",
                "message": "No se pudo identificar la acción pendiente; no se ejecutó ninguna operación.",
            }
        return self.process_input(pending_message, confirmed_by_user=True)

    def _clear_pending_network(self) -> None:
        self._awaiting_network_cidr = False
        self._pending_network_address = None
        self._awaiting_network_adapter = False
        self._pending_network_cidr = None
        self._awaiting_network_selection = False
        self._pending_network_candidates = []

    @staticmethod
    def _is_local_network_request(text: str) -> bool:
        normalized = text.casefold()
        requests_current_network = re.search(
            r"\b(mi\s+red(?:\s+actual)?|red\s+actual|"
            r"identific\w*\s+(?:mi\s+)?red)\b",
            normalized,
        )
        asks_agent_to_check = re.search(
            r"\b(fijate|fíjate|mira|mirá|revisa|revisá|busca|buscá)\s+"
            r"(?:vos|tu|tú)\b",
            normalized,
        )
        describes_local_detection = (
            re.search(
                r"\b(realiz\w*|realic\w*|realis\w*|hacelo|hace\s+el\s+escaneo|"
                r"detect\w*|encuentr\w*)\b",
                normalized,
            )
            and re.search(
                r"\b(vos|tu|t[uú]|automatic\w*|mi\s+red|la\s+red|por\s+mi)\b",
                normalized,
            )
        )
        return bool(
            requests_current_network or asks_agent_to_check or describes_local_detection
        )

    def _detect_local_networks(self) -> Dict[str, Any]:
        try:
            interfaces = os_adapter.get_private_network_interfaces()
        except (OSError, RuntimeError, ValueError) as exc:
            return {
                "type": "chat",
                "message": f"No pude consultar las interfaces de red locales: {exc}",
            }

        candidates = []
        private_ranges = (
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
        )
        for interface in interfaces:
            try:
                network = ipaddress.ip_network(interface["cidr"], strict=False)
            except (KeyError, TypeError, ValueError):
                continue
            if (
                network.version == 4
                and any(network.subnet_of(private) for private in private_ranges)
                and network.num_addresses <= 256
            ):
                candidates.append({**interface, "cidr": str(network)})

        if not candidates:
            return {
                "type": "chat",
                "message": (
                    "No encontré una interfaz local activa con una subred IPv4 privada "
                    "de hasta 256 direcciones que pueda ofrecer para este descubrimiento. "
                    "No se ejecutó ningún escaneo. Puedes indicar un CIDR privado "
                    "autorizado de hasta 256 direcciones."
                ),
            }

        self._awaiting_network_cidr = False
        self._pending_network_address = None
        self._pending_network_candidates = candidates
        self._awaiting_network_selection = True
        options = "\n".join(
            f"{index}. {item['name']}: `{item['cidr']}` (IPv4 {item['address']})"
            for index, item in enumerate(candidates, start=1)
        )
        return {
            "type": "chat",
            "message": (
                "Consulté las interfaces locales; no inicié Kali ni escaneé la red. "
                "Elige exactamente cuál quieres analizar respondiendo con su número o "
                "nombre de adaptador:\n\n"
                f"{options}\n\n"
                "Puede haber interfaces virtuales (WSL, Docker o Hyper-V); elige el "
                "segmento objetivo. Después pediré autorización explícita para el "
                "descubrimiento `nmap -sn`."
            ),
        }

    def _handle_network_selection(
        self,
        text: str,
        confirmed_by_user: bool,
    ) -> Dict[str, Any]:
        explicit_cidr = self._network_cidr_from_input(text)
        if explicit_cidr and "/" in text:
            self._clear_pending_network()
            return self._handle_kali_network_discovery(explicit_cidr, confirmed_by_user)

        selected = None
        if text.strip().isdecimal():
            index = int(text.strip()) - 1
            if 0 <= index < len(self._pending_network_candidates):
                selected = self._pending_network_candidates[index]
        else:
            normalized = text.casefold()
            named = [
                item for item in self._pending_network_candidates
                if item["name"].casefold() in normalized
            ]
            if len(named) == 1:
                selected = named[0]
            elif len(self._pending_network_candidates) == 1 and self._is_confirmation(text):
                selected = self._pending_network_candidates[0]

        if not selected:
            options = ", ".join(
                f"{index}: {item['name']} ({item['cidr']})"
                for index, item in enumerate(self._pending_network_candidates, start=1)
            )
            return {
                "type": "chat",
                "message": f"No pude identificar el adaptador. Elige uno de estos: {options}.",
            }

        self._pending_network_candidates = []
        self._awaiting_network_selection = False
        self._awaiting_network_cidr = False
        self._pending_network_address = None
        result = self._handle_kali_network_discovery(selected["cidr"], confirmed_by_user)
        if result.get("type") == "confirmation_required":
            result["message"] = (
                f"Interfaz seleccionada: {selected['name']} (`{selected['cidr']}`).\n\n"
                f"{result.get('message', 'Autoriza explícitamente el descubrimiento.')}"
            )
        return result

    def _request_network_adapter(self, cidr: str) -> Dict[str, Any]:
        self._awaiting_network_adapter = True
        self._pending_network_cidr = cidr
        return {
            "type": "chat",
            "message": (
                f"Con la IPv4 y máscara indicadas, el rango calculado es `{cidr}`. "
                "Antes de pedir autorización de escaneo, dime de qué adaptador obtuviste "
                "esos datos (por ejemplo, Wi-Fi o Ethernet). Una IPv4 de WSL, Docker o "
                "Hyper-V puede ser una red virtual distinta de tu LAN; no voy a asumir "
                "qué segmento quieres analizar."
            ),
        }

    def _handle_network_adapter_answer(self, text: str) -> Dict[str, Any]:
        normalized = text.casefold()
        virtual_markers = ("wsl", "docker", "hyper-v", "hyperv", "vethernet")
        if any(marker in normalized for marker in virtual_markers):
            if self._explicitly_selects_stated_network(normalized):
                cidr = self._pending_network_cidr
                self._clear_pending_network()
                if cidr:
                    return self._handle_kali_network_discovery(cidr, False)
            return {
                "type": "chat",
                "message": (
                    f"`{text}` parece identificar una interfaz virtual (por ejemplo, WSL, "
                    "Docker o Hyper-V). No puedo asumir que sea la LAN Wi-Fi. Indica si "
                    "quieres analizar precisamente ese segmento (por ejemplo, "
                    "`analizar ese segmento`) o proporciona la IPv4 y máscara del "
                    "adaptador Wi-Fi/Ethernet que sí quieres analizar."
                ),
            }

        if self._is_confirmation(text):
            return self._network_adapter_prompt()
        if re.search(r"\b(wi[\s-]?fi|inal[aá]mbric[oa]s?|ethernet|lan)\b", normalized):
            cidr = self._pending_network_cidr
            self._clear_pending_network()
            if cidr:
                result = self._handle_kali_network_discovery(cidr, False)
                if result.get("type") == "confirmation_required":
                    message = result.get(
                        "message",
                        f"Se requiere autorización para el descubrimiento en {cidr}.",
                    )
                    result["message"] = f"Adaptador indicado: {text}.\n\n{message}"
                return result
        return self._network_adapter_prompt()

    @staticmethod
    def _explicitly_selects_stated_network(text: str) -> bool:
        return bool(
            re.search(
                r"\b(analizar ese segmento|ese es el (?:segmento|rango|objetivo)|"
                r"quiero analizarlo|es la red que quiero analizar)\b",
                text,
            )
        )

    @staticmethod
    def _network_adapter_prompt() -> Dict[str, Any]:
        return {
            "type": "chat",
            "message": (
                "Necesito identificar el adaptador antes de continuar. Indica `Wi-Fi` o "
                "`Ethernet`, o aclara explícitamente si quieres analizar un segmento virtual."
            ),
        }

    def _dispatch_intent(self, intent: Dict[str, Any], confirmed: bool) -> Dict[str, Any]:
        action = intent.get("action")
        if action == "help":
            return self._handle_help()
        if action == "kali_capabilities":
            return {"type": "chat", "message": self._kali_capabilities_text()}
        if action == "kali_unsupported_operation":
            return {
                "type": "chat",
                "message": (
                    "No puedo ejecutar ni preparar ataques, explotación o escaneos de "
                    "vulnerabilidades. Las funciones de Kali disponibles en Anonymous "
                    "son:\n\n" + self._kali_capabilities_text()
                ),
            }
        if action == "status":
            return self._handle_status()
        if action == "ptt":
            return self._handle_ptt()
        if action == "ptt_reset":
            ptt_engine.reset_tree()
            return {"type": "ptt_reset", "message": "Árbol de tareas PTT reiniciado a estado inicial."}
        if action == "findings":
            return self._handle_findings()
        if action == "vulnerability_summary":
            return self._handle_vulnerability_summary(intent.get("query") or "")
        if action == "ping":
            return self._handle_ping(intent.get("target") or "127.0.0.1", confirmed)
        if action == "report":
            return self._handle_report()
        if action == "scan":
            return self._handle_scan(
                intent.get("target") or "127.0.0.1",
                intent.get("ports"),
                confirmed,
            )
        if action == "kali_network_discovery":
            target = intent.get("target")
            if not target:
                self._awaiting_network_cidr = True
                if intent.get("local_network"):
                    return self._detect_local_networks()
                return self._network_cidr_prompt()
            return self._handle_kali_network_discovery(target, confirmed)
        if action == "rag":
            return self._handle_rag(intent.get("query") or "seguridad")
        if action and str(action).startswith("kali"):
            return self._handle_kali_intent(intent, confirmed)
        return self._handle_ai_query(str(intent))

    def _handle_help(self) -> Dict[str, Any]:
        help_text = (
            "🛠️ **Comandos Disponibles en Anonymous:**\n\n"
            "• `status` / `briefing` : Estado del sistema, IP local y resumen de tareas.\n"
            "• `scan <ip>`           : Escaneo de puertos TCP nativo.\n"
            "• `ping <host>`         : Verifica conectividad.\n"
            "• `rag <consulta>`      : Base defensiva (OWASP, MITRE, CIS).\n"
            "• `ptt` / `ptt reset`   : Árbol de tareas de pentesting.\n"
            "• `findings`            : Hallazgos de la sesión.\n"
            "• `report`              : Resumen defensivo de hallazgos + PTT.\n"
            "• `kali status`         : Estado del contenedor forense y del MCP opcional.\n"
            "• `kali start`/`stop`   : Inicia o detiene el contenedor forense (HITL).\n"
            "• `kali forensic tools` : Consultas integradas de análisis forense de solo lectura.\n"
            "• `kali forensic <op> <archivo>`: Consulta una evidencia; `hash` guarda un informe en Resultados.\n"
            "• `kali-start <ip>`     : Sesión pasiva (carpeta de evidencias).\n"
            "• `kali discover <CIDR>`: Descubrimiento de hosts con Kali (CIDR privado, confirmación).\n"
            "• `kali knowledge <t>`  : Busca playbooks markdown copiados de kali-mcp.\n"
            "• `kali-finish`         : Cierra la sesión Kali.\n"
            "• `help` / `comandos`   : Esta ayuda.\n\n"
            "También entendés lenguaje natural, por ejemplo:\n"
            "`escaneá localhost`, `está vivo 127.0.0.1`, `qué dice OWASP sobre inyección SQL`,\n"
            "`levantá kali`, `estado de kali`, `playbook ssh`."
        )
        return {"type": "help", "message": help_text}

    @staticmethod
    def _kali_capabilities_text() -> str:
        return (
            "• Descubrimiento de hosts con `kali discover <CIDR>`: solo redes privadas "
            "de hasta 256 direcciones, únicamente `nmap -sn` y con confirmación explícita. "
            "No evalúa puertos, servicios ni vulnerabilidades.\n"
            "• Forense de solo lectura con `kali forensic tools` y las operaciones "
            "integradas sobre evidencias.\n"
            "• Estado con `kali status` y consulta de playbooks con `kali knowledge <tema>`.\n\n"
            "El contenedor forense y el servicio Kali MCP son componentes separados. "
            "No se admiten comandos arbitrarios, scripts de ataque ni escaneos de "
            "vulnerabilidades."
        )

    def _handle_status(self) -> Dict[str, Any]:
        briefing = briefing_engine.get_briefing()
        return {
            "type": "status",
            "message": briefing["summary_text"],
            "data": briefing,
        }

    def _handle_ptt(self) -> Dict[str, Any]:
        tasks = ptt_engine.get_all_tasks()
        return {
            "type": "ptt",
            "tasks": tasks,
            "message": "Árbol de Tareas de Pentesting (PTT) recuperado.",
        }

    def _handle_findings(self) -> Dict[str, Any]:
        findings = session_manager.get_findings(limit=15)
        return {
            "type": "findings",
            "findings": findings,
            "message": f"{len(findings)} hallazgos registrados en la sesión actual.",
        }

    def _handle_vulnerability_summary(self, question: str) -> Dict[str, Any]:
        context = self._last_discovery_context or {}
        target = context.get("target")
        facts = context.get("facts")
        answer = ollama_client.answer_kali_question(
            question,
            target if isinstance(target, str) else None,
            facts if isinstance(facts, dict) else None,
        )
        if answer:
            return {
                "type": "chat",
                "message": (
                    f"{answer}\n\nNota: una respuesta de Ollama no confirma hallazgos; "
                    "el descubrimiento de hosts no evalúa vulnerabilidades."
                ),
            }
        return {
            "type": "chat",
            "message": (
                "Ollama no respondió. Con la información actual no puedo determinar qué equipos son más "
                "vulnerables. El descubrimiento de hosts (`nmap -sn`) solo indica qué "
                "direcciones respondieron; no identifica servicios, versiones ni "
                "vulnerabilidades. Anonymous no ejecutará comandos arbitrarios ni "
                "un escaneo automático de vulnerabilidades. Si ya hiciste un análisis "
                "autorizado, consulta `findings` o `report`: sus resultados son señales "
                "para revisar, no vulnerabilidades confirmadas."
            ),
        }

    def _handle_ping(self, target: str, confirmed: bool = False) -> Dict[str, Any]:
        eval_res = agent_shield.evaluate_action("host_ping", {"target": target})
        if eval_res["requires_confirmation"] and not confirmed:
            return {
                "type": "confirmation_required",
                "action": "host_ping",
                "target": target,
                "risk_level": eval_res["risk_level"],
                "reason": eval_res["reason"],
                "pending_message": f"ping {target}",
                "message": (
                    f"⚠️ [AgentShield] Se requiere confirmación para hacer ping a '{target}' "
                    f"(Nivel de riesgo: {eval_res['risk_level']}).\n"
                    f"Razón: {eval_res['reason']}"
                ),
            }
        res = recon_engine.ping_host(target)
        msg = f"Host {target} {'está ACTIVO 🟢' if res['alive'] else 'NO responde 🔴'}"
        return {
            "type": "ping",
            "alive": res["alive"],
            "target": target,
            "message": msg,
            "output": res["output"],
        }

    def _handle_scan(self, target: str, ports_arg: Optional[str], confirmed: bool) -> Dict[str, Any]:
        eval_res = agent_shield.evaluate_action("port_scan", {"target": target})
        if eval_res["requires_confirmation"] and not confirmed:
            return {
                "type": "confirmation_required",
                "action": "port_scan",
                "target": target,
                "risk_level": eval_res["risk_level"],
                "reason": eval_res["reason"],
                "pending_message": f"scan {target}" + (f" {ports_arg}" if ports_arg else ""),
                "message": (
                    f"⚠️ [AgentShield] Se requiere confirmación para escanear '{target}' "
                    f"(Nivel de riesgo: {eval_res['risk_level']}).\n"
                    f"Razón: {eval_res['reason']}\n"
                    f"¿Deseas autorizar la ejecución?"
                ),
            }

        ports = None
        if ports_arg:
            ports = [int(p.strip()) for p in ports_arg.split(",") if p.strip().isdigit()] or None

        ptt_engine.update_status("recon-01", TaskStatus.COMPLETED, f"Objetivo fijado: {target}")

        scan_result = recon_engine.scan_ports(target, ports)
        open_count = scan_result["open_count"]
        msg = (
            f"Escaneo finalizado en {target}.\n"
            f"Puertos analizados: {scan_result['total_scanned']} | Abiertos: {open_count}"
        )

        banners = [p for p in scan_result.get("ports", []) if p.get("banner")]
        ptt_engine.update_status(
            "scan-02",
            TaskStatus.COMPLETED,
            f"Banner grabbing: {len(banners)} banner(s) en {open_count} puerto(s) abierto(s).",
        )

        advice = rag_engine.query_with_advice(
            "puertos servicios configuracion" if scan_result.get("ports") else "hardening"
        )
        if scan_result.get("ports"):
            topics = " ".join(
                {p.get("service", "").split("(")[0].strip().lower() for p in scan_result["ports"]}
            )
            advice = rag_engine.query_with_advice(topics or "puertos servicios")

        ptt_engine.update_status(
            "vuln-01",
            TaskStatus.COMPLETED,
            "Cruce local con base RAG (OWASP/MITRE/CIS). Sin consulta CVE remota.",
        )
        exposed = [p["port"] for p in scan_result.get("ports", []) if p["port"] in (21, 23, 445, 3389)]
        ptt_engine.update_status(
            "vuln-02",
            TaskStatus.COMPLETED,
            (
                f"Servicios con exposición típica a revisar: {exposed}"
                if exposed
                else "Sin servicios clásicos de configuración insegura en el resultado."
            ),
        )
        ptt_engine.update_status(
            "rep-01",
            TaskStatus.COMPLETED,
            f"Resumen: {open_count} puerto(s) abierto(s) en {target}.",
        )
        msg = f"{msg}\n\n{advice}"

        return {
            "type": "scan",
            "data": scan_result,
            "advice": advice,
            "message": msg,
        }

    def _handle_report(self) -> Dict[str, Any]:
        findings = session_manager.get_findings(limit=20)
        tasks = ptt_engine.get_all_tasks()
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        lines = [
            f"📄 Reporte defensivo local ({completed}/{len(tasks)} tareas PTT completadas).",
            f"Hallazgos: {session_manager.count_findings()}.",
        ]
        for item in findings[:8]:
            lines.append(f"- [{item.get('severity')}] {item.get('target')}: {item.get('title')}")
        if not findings:
            lines.append("Todavía no hay hallazgos. Ejecutá `scan 127.0.0.1` en un objetivo propio.")
        return {"type": "status", "message": "\n".join(lines), "findings": findings, "tasks": tasks}

    def _handle_rag(self, query: str) -> Dict[str, Any]:
        advice = rag_engine.query_with_advice(query)
        results = rag_engine.search(query, top_k=2)
        return {
            "type": "rag",
            "query": query,
            "results": results,
            "message": advice,
        }

    def _handle_ai_query(self, text: str) -> Dict[str, Any]:
        session_manager.save_message("user", text)
        recent_history = context_budget.prune_history(
            session_manager.get_recent_messages(limit=12)
        )
        mode_prompt = SYSTEM_PROMPT
        lower = text.lower()
        if any(k in lower for k in ("red team", "pentest", "exploit", "recon")):
            mode_prompt = f"{SYSTEM_PROMPT}\n\n{RED_TEAM_PROMPT}"
        elif any(k in lower for k in ("blue team", "mitigar", "hardening", "owasp", "cis")):
            mode_prompt = f"{SYSTEM_PROMPT}\n\n{BLUE_TEAM_PROMPT}"

        ai_response = gemini_client.generate_response(
            prompt=text,
            system_instruction=mode_prompt,
            history=recent_history,
        )

        session_manager.save_message("assistant", ai_response)
        return {
            "type": "chat",
            "message": ai_response,
        }

    def _handle_kali_intent(self, intent: Dict[str, Any], confirmed: bool) -> Dict[str, Any]:
        action = intent.get("action")
        if action == "kali_status":
            return self._kali_status()
        if action == "kali_start_stack":
            return self._wrap_kali(
                kali_forensics_engine.start_container(confirmed),
                "kali start",
                confirmed,
            )
        if action == "kali_stop_stack":
            return self._wrap_kali(
                kali_forensics_engine.stop_container(confirmed),
                "kali stop",
                confirmed,
            )
        if action == "kali_session_start":
            return self._wrap_kali(
                kali_mcp_engine.start_session(intent.get("target") or "127.0.0.1"),
                "kali-start",
                True,
            )
        if action == "kali_finish":
            return self._wrap_kali(kali_mcp_engine.finish_session(), "kali-finish", True)
        if action == "kali_knowledge":
            return self._wrap_kali(kali_mcp_engine.search_knowledge(intent.get("query") or ""), "kali knowledge", True)
        if action == "kali_audit":
            return self._wrap_kali(kali_mcp_engine.refuse_audit(), "kali-audit", True)
        return self._handle_kali("kali status", confirmed)

    def _handle_kali(self, text: str, confirmed: bool) -> Dict[str, Any]:
        parts = text.split()
        head = parts[0].lower() if parts else "kali"
        if head in ("kali-start", "kalistart"):
            target = parts[1] if len(parts) > 1 else "127.0.0.1"
            return self._wrap_kali(kali_mcp_engine.start_session(target), text, True)
        if head == "kali-finish":
            return self._wrap_kali(kali_mcp_engine.finish_session(), text, True)
        if head == "kali-audit":
            return self._wrap_kali(kali_mcp_engine.refuse_audit(), text, True)
        sub = parts[1].lower() if len(parts) > 1 else "status"
        rest = " ".join(parts[2:])
        if sub in ("status", "estado", "health", "salud"):
            return self._kali_status()
        if sub in ("start", "up", "levantar"):
            return self._wrap_kali(
                kali_forensics_engine.start_container(confirmed),
                "kali start",
                confirmed,
            )
        if sub in ("stop", "down", "parar"):
            return self._wrap_kali(
                kali_forensics_engine.stop_container(confirmed),
                "kali stop",
                confirmed,
            )
        if sub in ("forensic", "forense", "forensics"):
            operation = parts[2].lower() if len(parts) > 2 else "tools"
            if operation in ("tools", "herramientas", "help", "ayuda"):
                return {"type": "kali_forensics", "message": kali_forensics_engine.tools_text()}
            if len(parts) < 4:
                return {
                    "type": "chat",
                    "message": (
                        "Uso: `kali forensic <operación> <archivo>`.\n"
                        "Consulta `kali forensic tools` para ver las operaciones permitidas."
                    ),
                }
            result = kali_forensics_engine.analyze(operation, " ".join(parts[3:]))
            return {
                "type": "kali_forensics" if result.get("ok") else "chat",
                "message": str(result.get("message", result)),
                "data": result,
            }
        if sub in ("knowledge", "docs", "playbook", "wiki"):
            return self._wrap_kali(kali_mcp_engine.search_knowledge(rest or "index"), "kali knowledge", True)
        if sub in ("discover", "discovery"):
            target = parts[2] if len(parts) > 2 else ""
            return self._handle_kali_network_discovery(target, confirmed)
        if sub in ("exec", "execute", "run"):
            return self._wrap_kali(kali_mcp_engine.refuse_exec(rest), "kali exec", True)
        if sub == "start-session" or (sub == "session" and rest.startswith("start")):
            target = parts[-1] if len(parts) > 2 else "127.0.0.1"
            return self._wrap_kali(kali_mcp_engine.start_session(target), text, True)
        return self._kali_status()

    @staticmethod
    def _kali_status() -> Dict[str, Any]:
        forensics = kali_forensics_engine.status()
        mcp = kali_mcp_engine.mcp_health()
        data = {"forensics": forensics, "mcp": mcp}
        message = (
            "🐉 Kali forense\n"
            f"• Contenedor: {forensics['container']} ({forensics['state']})\n"
            f"• Conexión Docker: {'activa' if forensics['connected'] else 'no disponible'} "
            f"({forensics['detail']})\n"
            f"• Evidencias de solo lectura: {kali_forensics_engine.evidence_dir}\n"
            f"• Resultados: {kali_forensics_engine.results_dir}\n"
            f"• MCP opcional ({kali_mcp_engine.mcp_url}): "
            f"{'conectado' if mcp['healthy'] else 'no conectado'} ({mcp['detail']})\n"
            "• Anonymous solo envía operaciones forenses permitidas; no comandos arbitrarios."
        )
        return {"type": "status", "message": message, "data": data}

    def _handle_kali_network_discovery(self, target: str, confirmed: bool) -> Dict[str, Any]:
        result = kali_mcp_engine.discover_network(target, confirmed)
        if result.get("type") == "confirmation_required" and not confirmed:
            return result
        if result.get("ok") and result.get("type") == "kali_discovery":
            facts = result.get("interpretation_facts")
            self._last_discovery_context = {
                "target": target,
                "facts": facts if isinstance(facts, dict) else {},
            }
            interpretation = (
                ollama_client.interpret_network_discovery(target, facts)
                if isinstance(facts, dict)
                else None
            )
            if interpretation:
                result["interpretation_source"] = "Ollama"
                result["message"] += f"\n\nInterpretación de Ollama:\n{interpretation}"
            elif isinstance(facts, dict):
                result["interpretation_source"] = "local"
                result["message"] += f"\n\n{self._local_discovery_interpretation(facts)}"
        return {
            "type": result.get("type", "chat") if result.get("ok") else "chat",
            "message": result.get("message", str(result)),
            "data": result,
        }

    @staticmethod
    def _network_cidr_prompt() -> Dict[str, Any]:
        return {
            "type": "chat",
            "message": (
                "Entendido: solo haremos descubrimiento de hosts, sin escanear puertos. "
                "Para continuar necesito el rango CIDR privado autorizado, por ejemplo "
                "`192.168.0.0/24`. En Windows, para analizar tu LAN Wi-Fi, ejecuta `ipconfig` "
                "y pega aquí la IPv4 y máscara del adaptador Wi-Fi activo (no una interfaz "
                "virtual WSL/Docker/Hyper-V); Anonymous calculará el CIDR. Si solo envías la "
                "IPv4, guardaré ese dato y te pediré la máscara. También puedes decir "
                "`identifica mi red` para que liste las interfaces privadas activas y te "
                "permita elegir. Este paso solo descubre hosts: no evalúa ni clasifica "
                "vulnerabilidades. Después te pediré confirmación antes de ejecutar Kali."
            ),
        }

    @staticmethod
    def _is_discovery_followup(text: str) -> bool:
        normalized = text.casefold()
        asks_about_count = bool(
            re.search(r"\b(cu[aá]nt[oa]s?|n[uú]mero\s+de)\b", normalized)
            and re.search(r"\b(dispositivos?|equipos?|hosts?|m[aá]quinas?)\b", normalized)
        )
        asks_if_count_is_devices = bool(
            re.search(r"\b(dispositivos?|equipos?|hosts?|m[aá]quinas?)\b", normalized)
            and re.search(r"\b(son|es|significa|quiere\s+decir|corresponde)\b", normalized)
        )
        refers_to_last_result = bool(
            re.search(r"\b(entonces|resultado|esos?|esas?|los|las|ah[ií])\b", normalized)
        )
        return asks_about_count or (asks_if_count_is_devices and refers_to_last_result)

    @staticmethod
    def _answer_discovery_followup(
        context: Dict[str, Any],
        question: str,
    ) -> Dict[str, Any]:
        target = context.get("target", "la red analizada")
        facts = context.get("facts")
        if not isinstance(facts, dict) or not facts:
            answer = (
                f"No tengo datos estructurados suficientes del descubrimiento de `{target}` "
                "para determinar cuántos dispositivos respondieron. No voy a inferir un "
                "conteo a partir de información incompleta."
            )
        else:
            answer = ollama_client.answer_kali_question(
                question,
                str(target),
                facts,
            )
            if not answer:
                echo_replies = facts.get("confirmed_echo_replies")
                reported_up = facts.get("reported_up")
                uncertain_resets = facts.get("uncertain_tcp_resets")
                if echo_replies is None:
                    evidence = "Los datos guardados no indican cuántas respuestas echo-reply hubo."
                else:
                    evidence = (
                        f"{echo_replies} IP respondieron con `echo-reply`, lo que es evidencia "
                        "de que algo respondió en esas direcciones."
                    )
                additional = ""
                if uncertain_resets:
                    additional = (
                        f" Nmap reportó {reported_up} hosts activos, pero {uncertain_resets} "
                        "respuestas fueron TCP reset y podrían proceder de una puerta de enlace "
                        "o intermediario."
                    )
                answer = (
                    "Ollama no respondió. "
                    f"No necesariamente. {evidence}{additional} "
                    "Eso no confirma por sí solo el mismo número de dispositivos físicos ni "
                    "permite identificar cuáles son desconocidos. Verifica las IP en la lista "
                    "de clientes del router o contra tu inventario."
                )
        return {"type": "chat", "message": answer}

    @staticmethod
    def _single_ipv4_from_input(text: str) -> Optional[str]:
        addresses = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
        if len(addresses) != 1:
            return None
        try:
            return str(ipaddress.IPv4Address(addresses[0]))
        except ipaddress.AddressValueError:
            return None

    @staticmethod
    def _network_mask_prompt(address: str) -> Dict[str, Any]:
        return {
            "type": "chat",
            "message": (
                f"Recibí la IPv4 `{address}`, pero todavía no puedo determinar su subred. "
                "Pega también la máscara de subred del mismo adaptador que aparece en "
                "`ipconfig` (por ejemplo `255.255.255.0`). Para escanear tu LAN Wi-Fi, "
                "asegúrate de usar la dirección del adaptador Wi-Fi y no la de una interfaz "
                "virtual WSL/Docker/Hyper-V. No ejecutaré Kali hasta validar el rango y "
                "pedirte confirmación."
            ),
        }

    @staticmethod
    def _network_cidr_from_input(text: str) -> Optional[str]:
        cidrs = re.findall(
            r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}(?!\d)",
            text,
        )
        if len(cidrs) == 1:
            try:
                return str(ipaddress.ip_network(cidrs[0], strict=False))
            except ValueError:
                return None

        addresses = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
        if len(addresses) != 2:
            return None
        try:
            interface = ipaddress.IPv4Interface(f"{addresses[0]}/{addresses[1]}")
        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            return None
        return str(interface.network)

    @staticmethod
    def _is_confirmation(text: str) -> bool:
        normalized = text.strip().lower().strip(" .,!¡¿?")
        return normalized in {
            "s",
            "si",
            "sí",
            "yes",
            "confirmo",
            "comfirmo",
            "confirmar",
            "confirmado",
            "autorizo",
        }

    @staticmethod
    def _local_discovery_interpretation(facts: Dict[str, Any]) -> str:
        reported = facts.get("reported_up")
        echo_replies = facts.get("confirmed_echo_replies")
        uncertain_resets = facts.get("uncertain_tcp_resets")
        lines = ["Interpretación local (Ollama no disponible):"]
        if reported is not None:
            lines.append(f"Nmap informó {reported} hosts como activos.")
        if echo_replies is not None:
            lines.append(f"{echo_replies} respondieron con echo-reply.")
        if uncertain_resets:
            lines.append(
                f"{uncertain_resets} respuestas fueron TCP reset; podrían generarlas "
                "una puerta de enlace o un intermediario y no prueban que sean dispositivos."
            )
        lines.append(
            "El descubrimiento no identifica qué equipos son desconocidos; compara las IP "
            "con el inventario o la lista de clientes del router."
        )
        return "\n".join(lines)

    def _wrap_kali(self, result: Dict[str, Any], pending: str, confirmed: bool) -> Dict[str, Any]:
        if result.get("type") == "confirmation_required" and not confirmed:
            result["pending_message"] = pending
            result["risk_level"] = "MEDIUM"
            return result
        return {
            "type": "status" if result.get("ok", True) else "chat",
            "message": result.get("message", str(result)),
            "data": result,
        }


dispatcher = Dispatcher()
