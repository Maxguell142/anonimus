"""
AgentShield - Security Guardrail & Safety Gate (Inspired by ECC & OpenJarvis).
Inspects commands and actions, classifying risk levels and enforcing Human-In-The-Loop (HITL).
"""

from typing import Dict, Any, Tuple
import re


class RiskLevel:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def is_local_target(target: str) -> bool:
    host = (target or "").strip().lower()
    return host in ("127.0.0.1", "localhost", "0.0.0.0", "::1")


class AgentShield:
    """Security filter to prevent dangerous or unintended command execution."""

    DANGEROUS_PATTERNS = [
        (r"\b(rm\s+-rf|del\s+/f|format|mkfs|dd\s+if=)\b", RiskLevel.CRITICAL, "Comando destructivo del sistema de archivos"),
        (r"\b(nc\s+-e|bash\s+-i|/dev/tcp/|powershell\s+.*-enc)\b", RiskLevel.HIGH, "Patrón de Reverse Shell o ejecución arbitraria ofuscada"),
        (r"\b(iptables\s+-F|netsh\s+advfirewall\s+set\s+allprofiles\s+state\s+off)\b", RiskLevel.HIGH, "Desactivación de firewall o reglas de red"),
        (r"\b(nmap|masscan|hydra|sqlmap|nikto)\b", RiskLevel.MEDIUM, "Herramienta ofensiva / escaneo de red"),
        (r"\b(ping|traceroute|tracert|whois|nslookup|dig)\b", RiskLevel.LOW, "Comando de diagnóstico de red pasivo"),
    ]

    def __init__(self, safe_mode: bool = True):
        self.safe_mode = safe_mode

    def evaluate_command(self, command_str: str) -> Dict[str, Any]:
        """Evaluates command string and returns risk assessment."""
        cmd_lower = command_str.lower().strip()

        for pattern, risk, reason in self.DANGEROUS_PATTERNS:
            if re.search(pattern, cmd_lower):
                return {
                    "allowed": risk != RiskLevel.CRITICAL,
                    "risk_level": risk,
                    "requires_confirmation": risk in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL),
                    "reason": reason,
                    "command": command_str,
                }

        # Default fallback: safe read/info action
        return {
            "allowed": True,
            "risk_level": RiskLevel.LOW,
            "requires_confirmation": False,
            "reason": "Comando operativo estándar de bajo riesgo",
            "command": command_str,
        }

    def evaluate_action(self, action_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates structured internal actions (e.g. port_scan, exploit_check)."""
        if action_type == "port_scan":
            target = details.get("target", "localhost")
            local = is_local_target(target)
            return {
                "allowed": True,
                "risk_level": RiskLevel.LOW if local else RiskLevel.MEDIUM,
                "requires_confirmation": not local,
                "reason": f"Escaneo de puertos en objetivo: {target}",
            }
        if action_type == "host_ping":
            target = details.get("target", "localhost")
            local = is_local_target(target)
            return {
                "allowed": True,
                "risk_level": RiskLevel.LOW if local else RiskLevel.MEDIUM,
                "requires_confirmation": not local,
                "reason": f"Ping ICMP hacia: {target}",
            }
        elif action_type == "exploit_verify":
            return {
                "allowed": True,
                "risk_level": RiskLevel.HIGH,
                "requires_confirmation": True,
                "reason": "Verificación activa de vulnerabilidad o prueba de concepto",
            }
        elif action_type in ("rag_query", "daily_briefing", "system_info", "ptt_view"):
            return {
                "allowed": True,
                "risk_level": RiskLevel.LOW,
                "requires_confirmation": False,
                "reason": "Acción defensiva o de consulta de información",
            }

        return {
            "allowed": True,
            "risk_level": RiskLevel.LOW,
            "requires_confirmation": False,
            "reason": "Operación general",
        }


# Global AgentShield instance
agent_shield = AgentShield()
