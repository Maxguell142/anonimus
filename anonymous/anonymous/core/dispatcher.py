"""
Core Request Dispatcher for Anonymous.
Coordinates AgentShield guardrails, Gemini brain, Red/Blue engines, and Session persistence.
"""

from typing import Dict, Any, Optional
from anonymous.core.session import session_manager
from anonymous.core.intent import parse_intent
from anonymous.guardrails.agent_shield import agent_shield
from anonymous.guardrails.context_budget import context_budget
from anonymous.brain.gemini_client import gemini_client
from anonymous.brain.prompts import SYSTEM_PROMPT, RED_TEAM_PROMPT, BLUE_TEAM_PROMPT
from anonymous.engines.red.recon import recon_engine
from anonymous.engines.red.ptt import ptt_engine, TaskStatus
from anonymous.engines.blue.rag_engine import rag_engine
from anonymous.engines.ops.briefing import briefing_engine


class Dispatcher:
    """Central orchestrator for Anonymous requests."""

    def process_input(self, user_text: str, confirmed_by_user: bool = False) -> Dict[str, Any]:
        text = user_text.strip()
        if not text:
            return {"type": "empty", "message": "Por favor escribe un comando o consulta."}

        parts = text.split()
        cmd = parts[0].lower()

        if cmd in ("help", "ayuda", "?"):
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
            ports_arg = parts[2] if len(parts) > 2 else None
            return self._handle_scan(target, ports_arg, confirmed_by_user)
        if cmd in ("rag", "normativa"):
            query = " ".join(parts[1:]) if len(parts) > 1 else "seguridad"
            return self._handle_rag(query)

        intent = parse_intent(text)
        if intent:
            return self._dispatch_intent(intent, confirmed_by_user)

        return self._handle_ai_query(text)

    def _dispatch_intent(self, intent: Dict[str, Any], confirmed: bool) -> Dict[str, Any]:
        action = intent.get("action")
        if action == "help":
            return self._handle_help()
        if action == "status":
            return self._handle_status()
        if action == "ptt":
            return self._handle_ptt()
        if action == "ptt_reset":
            ptt_engine.reset_tree()
            return {"type": "ptt_reset", "message": "Árbol de tareas PTT reiniciado a estado inicial."}
        if action == "findings":
            return self._handle_findings()
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
        if action == "rag":
            return self._handle_rag(intent.get("query") or "seguridad")
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
            "• `help`                : Esta ayuda.\n\n"
            "También entendés lenguaje natural, por ejemplo:\n"
            "`escaneá localhost`, `está vivo 127.0.0.1`, `qué dice OWASP sobre inyección SQL`."
        )
        return {"type": "help", "message": help_text}

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


dispatcher = Dispatcher()
