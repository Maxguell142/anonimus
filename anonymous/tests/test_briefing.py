import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.engines.ops.briefing import BriefingEngine


class TestBriefing(unittest.TestCase):
    def test_briefing_reports_forensic_container_separately_from_optional_mcp(self):
        with (
            patch(
                "anonymous.engines.ops.briefing.os_adapter.get_system_info",
                return_value={
                    "os": "Windows",
                    "sys_platform": "win32",
                    "hostname": "test-host",
                    "local_ip": "127.0.0.1",
                },
            ),
            patch(
                "anonymous.engines.ops.briefing.session_manager.get_findings",
                return_value=[],
            ),
            patch(
                "anonymous.engines.ops.briefing.session_manager.count_findings",
                return_value=0,
            ),
            patch(
                "anonymous.engines.ops.briefing.ptt_engine.get_all_tasks",
                return_value=[],
            ),
            patch(
                "anonymous.engines.ops.briefing.kali_mcp_engine.status",
                return_value={
                    "mcp_healthy": False,
                    "mcp_url": "http://127.0.0.1:666/mcp",
                },
            ),
            patch(
                "anonymous.engines.ops.briefing.kali_forensics_engine.status",
                return_value={
                    "connected": True,
                    "container": "kali-forensics",
                    "state": "running",
                    "detail": "ready",
                },
            ),
        ):
            result = BriefingEngine().get_briefing()

        self.assertTrue(result["kali_forensics"]["connected"])
        self.assertIn("Kali forense: running (conectado)", result["summary_text"])
        self.assertIn("Kali MCP opcional: abajo", result["summary_text"])


if __name__ == "__main__":
    unittest.main()
