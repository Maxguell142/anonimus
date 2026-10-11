"""
Operating System Adapter (OSAdapter).
Provides cross-platform abstraction for Windows and Linux without Docker dependencies.
"""

import sys
import os
import socket
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional


class OSAdapter:
    """Agnostic OS layer for Windows and Linux."""

    def __init__(self):
        self.is_windows = sys.platform.startswith("win")
        self.is_linux = sys.platform.startswith("linux")
        self.is_macos = sys.platform.startswith("darwin")
        self.platform_name = (
            "Windows" if self.is_windows else ("Linux" if self.is_linux else "macOS")
        )

    def get_system_info(self) -> Dict[str, Any]:
        """Returns baseline system and network information."""
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"

        return {
            "os": self.platform_name,
            "sys_platform": sys.platform,
            "python_version": sys.version.split()[0],
            "hostname": hostname,
            "local_ip": local_ip,
            "user": os.getenv("USERNAME" if self.is_windows else "USER", "unknown"),
        }

    def format_ping_command(self, host: str, count: int = 4) -> List[str]:
        """Adapts ping command syntax between Windows and Unix."""
        if self.is_windows:
            return ["ping", "-n", str(count), host]
        else:
            return ["ping", "-c", str(count), host]

    def execute_command(
        self, cmd: List[str], timeout: int = 15
    ) -> Dict[str, Any]:
        """Safely executes a system command and captures output."""
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
            )
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Comando superó el límite de tiempo de {timeout}s.",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "exit_code": 127,
                "stdout": "",
                "stderr": f"Herramienta no encontrada en el sistema: '{cmd[0]}'.",
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
            }


# Singleton instance
os_adapter = OSAdapter()
