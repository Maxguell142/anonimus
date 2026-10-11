"""
Core Request Dispatcher for Anonymous.
Coordinates AgentShield guardrails, Gemini brain, Red/Blue engines, and Session persistence.
"""

from typing import Dict, Any, Optional
from anonymous.core.session import session_manager
from anonymous.core.os_adapter import os_adapter
from anonymous.guardrails.agent_shield import agent_shield, RiskLevel
from anonymous.brain.gemini_client import gemini_client
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

        # 1. Direct Built-in Commands
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
            return self._handle_ping(target)

        if cmd in ("scan", "escanear"):
            target = parts[1] if len(parts) > 1 else "127.0.0.1"
            ports_arg = parts[2] if len(parts) > 2 else None
            return self._handle_scan(target, ports_arg, confirmed_by_user)

        if cmd in ("rag", "normativa"):
            query = " ".join(parts[1:]) if len(parts) > 1 else "seguridad"
            return self._handle_rag(query)

        # 2. General Natural Language Query (Processed through Brain)
        return self._handle_ai_query(text)

    def _handle_help(self) -> Dict[str, Any]:
        help_text = (
            "🛠️ **Comandos Disponibles en Anonymous:**\n\n"
            "• `status` / `briefing` : Muestra el estado del sistema, IP local y resumen de tareas.\n"
            "• `scan <ip>`           : Realiza un escaneo de puertos TCP rápido con Python nativo.\n"
            "• `ping <host>`         : Verifica conectividad de red con el host.\n"
            "• `rag <consulta>`      : Consulta la base defensiva de normativas (OWASP, MITRE, CIS).\n"
            "• `ptt`                 : Visualiza el estado actual del Pentesting Task Tree.\n"
            "• `ptt reset`           : Reinicia el árbol de tareas de pentesting.\n"
            "• `findings`            : Muestra la lista de vulnerabilidades y puertos detectados.\n"
            "• `help`                : Muestra esta ayuda.\n\n"
            "O simplemente escribe cualquier consulta en lenguaje natural para el asistente."
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

    def _handle_ping(self, target: str) -> Dict[str, Any]:
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
        # AgentShield Risk Verification
        eval_res = agent_shield.evaluate_action("port_scan", {"target": target})
        if eval_res["requires_confirmation"] and not confirmed:
            return {
                "type": "confirmation_required",
                "action": "port_scan",
                "target": target,
                "risk_level": eval_res["risk_level"],
                "reason": eval_res["reason"],
                "message": (
                    f"⚠️ [AgentShield] Se requiere confirmación para escanear '{target}' "
                    f"(Nivel de riesgo: {eval_res['risk_level']}).\n"
                    f"Razón: {eval_res['reason']}\n"
                    f"¿Deseas autorizar la ejecución? (S/n)"
                ),
            }

        ports = None
        if ports_arg:
            try:
                ports = [int(p.strip()) for p in ports_arg.split(",") if p.strip().isdigit()]
            except Exception:
                pass

        scan_result = recon_engine.scan_ports(target, ports)
        open_count = scan_result["open_count"]
        msg = (
            f"Escaneo finalizado en {target}.\n"
            f"Puertos analizados: {scan_result['total_scanned']} | Abiertos: {open_count}"
        )
        return {
            "type": "scan",
            "data": scan_result,
            "message": msg,
        }

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
        recent_history = session_manager.get_recent_messages(limit=6)

        ai_response = gemini_client.generate_response(
            prompt=text,
            history=recent_history
        )

        session_manager.save_message("assistant", ai_response)
        return {
            "type": "chat",
            "message": ai_response,
        }


dispatcher = Dispatcher()
