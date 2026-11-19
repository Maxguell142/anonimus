"""
Operating System Adapter (OSAdapter).
Provides cross-platform abstraction for Windows and Linux without Docker dependencies.
"""

import sys
import os
import ipaddress
import socket
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

import psutil


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

    def get_private_network_interfaces(self) -> List[Dict[str, str]]:
        """Return active interfaces with RFC1918 IPv4 addresses and their subnet."""
        stats = psutil.net_if_stats()
        interfaces = psutil.net_if_addrs()
        private_ranges = (
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
        )
        results: List[Dict[str, str]] = []

        for name, addresses in interfaces.items():
            interface_stats = stats.get(name)
            if not interface_stats or not interface_stats.isup:
                continue
            for address in addresses:
                if address.family != socket.AF_INET or not address.netmask:
                    continue
                try:
                    interface = ipaddress.IPv4Interface(
                        f"{address.address}/{address.netmask}"
                    )
                except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
                    continue
                if not any(interface.ip in network for network in private_ranges):
                    continue
                results.append(
                    {
                        "name": name,
                        "address": str(interface.ip),
                        "netmask": str(interface.netmask),
                        "cidr": str(interface.network),
                    }
                )
        return results

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
