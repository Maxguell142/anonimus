"""
Reconnaissance & Port Auditing Engine (Red Team).
Performs native Python socket scans without external binary dependencies.
"""

import socket
import concurrent.futures
from typing import List, Dict, Any, Tuple
from anonymous.core.os_adapter import os_adapter
from anonymous.core.session import session_manager
from anonymous.engines.red.ptt import ptt_engine, TaskStatus

COMMON_SERVICES = {
    21: "FTP (File Transfer Protocol)",
    22: "SSH (Secure Shell)",
    23: "Telnet (Insecure remote terminal)",
    25: "SMTP (Simple Mail Transfer)",
    53: "DNS (Domain Name System)",
    80: "HTTP (Web Server)",
    110: "POP3 (Post Office Protocol)",
    135: "MSRPC (Microsoft RPC Endpoint)",
    139: "NetBIOS-SSN",
    443: "HTTPS (Secure Web Server)",
    445: "SMB (Server Message Block / Windows Sharing)",
    1433: "MSSQL (Microsoft SQL Server)",
    3306: "MySQL (Database Server)",
    3389: "RDP (Remote Desktop Protocol)",
    5432: "PostgreSQL (Database Server)",
    6379: "Redis (In-memory Store)",
    8080: "HTTP-Proxy / Alternative Web",
    8443: "HTTPS-Alt",
}


class ReconEngine:
    """Network reconnaissance and port audit scanner."""

    def __init__(self, timeout: float = 0.6, max_workers: int = 50):
        self.timeout = timeout
        self.max_workers = max_workers

    def ping_host(self, target: str) -> Dict[str, Any]:
        """Pings target using cross-platform OSAdapter."""
        ptt_engine.update_status("recon-02", TaskStatus.IN_PROGRESS, f"Verificando host vivo en {target}")
        cmd = os_adapter.format_ping_command(target, count=2)
        res = os_adapter.execute_command(cmd, timeout=5)
        alive = res["success"] or ("TTL=" in res["stdout"].upper() or "BYTES=" in res["stdout"].upper())
        status = TaskStatus.COMPLETED if alive else TaskStatus.FAILED
        ptt_engine.update_status("recon-02", status, f"Host {'activo' if alive else 'no responde'}")
        return {
            "target": target,
            "alive": alive,
            "output": res["stdout"],
        }

    def _probe_port(self, host: str, port: int) -> Optional[Dict[str, Any]]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            res = s.connect_ex((host, port))
            if res == 0:
                service_desc = COMMON_SERVICES.get(port, "Desconocido")
                banner = ""
                try:
                    s.settimeout(0.5)
                    s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                    banner = s.recv(128).decode("latin-1", errors="ignore").strip().splitlines()[0]
                except Exception:
                    pass

                return {
                    "port": port,
                    "service": service_desc,
                    "banner": banner,
                    "state": "open",
                }
        except Exception:
            pass
        finally:
            s.close()
        return None

    def scan_ports(self, host: str, ports: Optional[List[int]] = None) -> Dict[str, Any]:
        """Scans specified ports or standard common ports."""
        if not ports:
            ports = sorted(list(COMMON_SERVICES.keys()))

        ptt_engine.update_status("scan-01", TaskStatus.IN_PROGRESS, f"Escaneando {len(ports)} puertos en {host}")

        open_ports = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._probe_port, host, port): port for port in ports}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    open_ports.append(result)

        open_ports.sort(key=lambda x: x["port"])

        # Record findings in session
        for p in open_ports:
            sev = "HIGH" if p["port"] in (21, 23, 445, 3389) else "MEDIUM"
            session_manager.record_finding(
                target=host,
                category="Port",
                title=f"Puerto {p['port']}/TCP abierto ({p['service']})",
                details=f"Banner: {p['banner']}" if p["banner"] else "Sin banner",
                severity=sev,
            )

        ptt_engine.update_status(
            "scan-01",
            TaskStatus.COMPLETED,
            f"Completado: {len(open_ports)} puertos abiertos detectados."
        )

        return {
            "target": host,
            "total_scanned": len(ports),
            "open_count": len(open_ports),
            "ports": open_ports,
        }


recon_engine = ReconEngine()
