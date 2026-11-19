"""Restricted OpenSSH transport for the configured cloud Kali host."""

from __future__ import annotations

import ipaddress
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


_USERNAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{0,31}\Z")
_HOST_LABEL_PATTERN = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z"
)
_HEALTH_COMMAND = "printf ANONYMOUS_KALI_SSH_OK"
_HEALTH_MARKER = "ANONYMOUS_KALI_SSH_OK"


class KaliSshTransport:
    """Runs only a health probe and bounded Nmap host discovery over SSH."""

    def __init__(self, connection: Dict[str, Any]) -> None:
        self.connection = dict(connection)

    def health_check(self) -> Dict[str, Any]:
        try:
            result = self._run("health")
        except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
            return {"healthy": False, "detail": str(exc)[:240]}
        if result.returncode != 0:
            return {"healthy": False, "detail": self._result_detail(result)}
        if (result.stdout or "").strip() != _HEALTH_MARKER:
            return {
                "healthy": False,
                "detail": "SSH respondió, pero el resultado de comprobación no coincide.",
            }
        return {
            "healthy": True,
            "detail": f"SSH conectado a {self._destination()} con host key verificada.",
        }

    def discover_network(self, target: str) -> Dict[str, Any]:
        try:
            result = self._run("discover", target=target)
        except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
            return {"ok": False, "detail": str(exc)[:240]}
        output = self._result_detail(result)
        if result.returncode != 0:
            return {"ok": False, "detail": output or "Nmap terminó con error."}
        return {"ok": True, "output": output}

    def _run(self, operation: str, target: Optional[str] = None) -> subprocess.CompletedProcess:
        if operation == "health":
            remote_command = _HEALTH_COMMAND
            timeout = 15
        elif operation == "discover":
            network = self._validated_network(target or "")
            remote_command = f"nmap -sn -n --reason {network}"
            timeout = 90
        else:
            raise ValueError("Operación SSH no permitida.")

        executable = shutil.which("ssh")
        if not executable:
            raise RuntimeError("No se encontró OpenSSH (`ssh`) en PATH.")
        connection_error = self._connection_error()
        if connection_error:
            raise ValueError(connection_error)

        command = [
            executable,
            "-F",
            "none",
            "-T",
            "-p",
            str(self.connection["port"]),
            "-i",
            str(self.connection["key_path"]),
            "-o",
            "BatchMode=yes",
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            "CheckHostIP=yes",
            "-o",
            f"UserKnownHostsFile={self.connection['known_hosts']}",
            "-o",
            "GlobalKnownHostsFile=none",
            "-o",
            "PasswordAuthentication=no",
            "-o",
            "KbdInteractiveAuthentication=no",
            "-o",
            "ClearAllForwardings=yes",
            "-o",
            "ForwardAgent=no",
            "-o",
            "ConnectTimeout=10",
            f"{self.connection['username']}@{self.connection['host']}",
            remote_command,
        ]
        try:
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                shell=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"SSH excedió el límite de {timeout} segundos.") from exc

    def _connection_error(self) -> str:
        host = self.connection.get("host")
        username = self.connection.get("username")
        port = self.connection.get("port")
        key_path = self.connection.get("key_path")
        known_hosts = self.connection.get("known_hosts")

        if not isinstance(host, str) or not self._valid_host(host):
            return "Configura un host SSH válido para Kali cloud."
        if not isinstance(username, str) or not _USERNAME_PATTERN.fullmatch(username):
            return "Configura un usuario SSH válido."
        if type(port) is not int or not 1 <= port <= 65535:
            return "El puerto SSH debe ser un entero entre 1 y 65535."
        if not isinstance(key_path, str) or not key_path.strip():
            return "Configura la ruta de la clave privada SSH."
        if not Path(key_path).is_file():
            return f"No se encontró el archivo de clave SSH: {key_path}"
        if not isinstance(known_hosts, str) or not known_hosts.strip():
            return "Configura el archivo known_hosts con la host key verificada."
        if not Path(known_hosts).is_file():
            return f"No se encontró el archivo known_hosts: {known_hosts}"
        return ""

    def _destination(self) -> str:
        return f"{self.connection.get('username', 'kali')}@{self.connection.get('host', '')}"

    @staticmethod
    def _valid_host(host: str) -> bool:
        if not host or len(host) > 253 or host != host.strip():
            return False
        try:
            return ipaddress.ip_address(host).version == 4
        except ValueError:
            return all(_HOST_LABEL_PATTERN.fullmatch(label) for label in host.split("."))

    @staticmethod
    def _validated_network(target: str) -> ipaddress.IPv4Network:
        if not target or "/" not in target:
            raise ValueError("Indicá un CIDR IPv4, por ejemplo `192.168.0.0/24`.")
        network = ipaddress.ip_network(target, strict=False)
        private_networks = (
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
        )
        if network.version != 4 or not any(network.subnet_of(item) for item in private_networks):
            raise ValueError("Solo se permite descubrir redes IPv4 privadas RFC1918.")
        if network.num_addresses > 256:
            raise ValueError("El alcance máximo permitido es una subred de 256 direcciones (/24).")
        return network

    @staticmethod
    def _result_detail(result: subprocess.CompletedProcess) -> str:
        return "\n".join(
            value.strip()
            for value in (result.stdout or "", result.stderr or "")
            if value and value.strip()
        )[-20000:]
