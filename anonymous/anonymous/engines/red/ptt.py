"""
Pentesting Task Tree (PTT) - Inspired by PentestGPT.
Tracks multi-phase penetration testing tasks and progress hierarchy.
"""

from typing import List, Dict, Any
from anonymous.core.session import session_manager


class TaskStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PentestTaskTree:
    """Manages the Pentesting Task Tree lifecycle."""

    DEFAULT_PHASES = [
        ("1. Reconnaissance", [
            ("recon-01", "Identificación de objetivo y resolución DNS"),
            ("recon-02", "Detección de host vivo (Ping/ICMP)"),
        ]),
        ("2. Scanning & Enumeration", [
            ("scan-01", "Escaneo de puertos TCP comunes"),
            ("scan-02", "Identificación y banner grabbing de servicios"),
        ]),
        ("3. Vulnerability Analysis", [
            ("vuln-01", "Cruce de servicios con base de datos CVE/RAG"),
            ("vuln-02", "Evaluación de configuraciones por defecto"),
        ]),
        ("4. Reporting & Remediation", [
            ("rep-01", "Generación de reporte técnico y plan de mitigación"),
        ]),
    ]

    def __init__(self):
        self._ensure_default_tree()

    def _ensure_default_tree(self):
        existing = session_manager.get_ptt_tasks()
        if not existing:
            for phase, tasks in self.DEFAULT_PHASES:
                for task_id, name in tasks:
                    session_manager.update_task(
                        task_id=task_id,
                        phase=phase,
                        name=name,
                        status=TaskStatus.PENDING,
                        details=""
                    )

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        return session_manager.get_ptt_tasks()

    def update_status(self, task_id: str, status: str, details: str = ""):
        tasks = self.get_all_tasks()
        target = next((t for t in tasks if t["id"] == task_id), None)
        if target:
            session_manager.update_task(
                task_id=task_id,
                phase=target["phase"],
                name=target["name"],
                status=status,
                details=details or target.get("details", "")
            )

    def reset_tree(self):
        for phase, tasks in self.DEFAULT_PHASES:
            for task_id, name in tasks:
                session_manager.update_task(
                    task_id=task_id,
                    phase=phase,
                    name=name,
                    status=TaskStatus.PENDING,
                    details=""
                )


ptt_engine = PentestTaskTree()
