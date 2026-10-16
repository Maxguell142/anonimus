"""
Daily Briefing & Health Monitor (Ops Engine - Inspired by OpenJarvis).
Generates system health, operational status, and security posture summaries.
"""

from typing import Dict, Any
from anonymous.core.os_adapter import os_adapter
from anonymous.core.session import session_manager
from anonymous.engines.red.ptt import ptt_engine


class BriefingEngine:
    """Provides status briefings and posture overviews."""

    def get_briefing(self) -> Dict[str, Any]:
        sys_info = os_adapter.get_system_info()
        findings = session_manager.get_findings(limit=5)
        findings_count = session_manager.count_findings()
        tasks = ptt_engine.get_all_tasks()

        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        in_progress_tasks = [t for t in tasks if t.get("status") == "in_progress"]

        summary_text = (
            f"📋 [Resumen Anonymous ⚡]\n"
            f"• Sistema: {sys_info['os']} ({sys_info['sys_platform']}) en {sys_info['hostname']}\n"
            f"• IP Local: {sys_info['local_ip']}\n"
            f"• Tareas PTT: {len(completed_tasks)}/{len(tasks)} completadas ({len(in_progress_tasks)} en progreso)\n"
            f"• Hallazgos registrados: {findings_count} eventos de seguridad guardados."
        )

        return {
            "system_info": sys_info,
            "findings_count": findings_count,
            "recent_findings": findings,
            "tasks_summary": {
                "total": len(tasks),
                "completed": len(completed_tasks),
                "in_progress": len(in_progress_tasks),
            },
            "summary_text": summary_text,
        }


briefing_engine = BriefingEngine()
