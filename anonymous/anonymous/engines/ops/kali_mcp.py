"""
Optional Kali MCP / Docker bridge for Anonymous.

Starts the existing kali-mcp-main compose stack, checks MCP health, searches
the copied knowledge markdown, and manages session folders.

Does not run exploit, brute-force, or payload tooling.
"""

from __future__ import annotations

import json
import ipaddress
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from anonymous.config import (
    KALI_MCP_ROOT,
    KALI_MCP_URL,
    KALI_SESSIONS_DIR,
    PROJECT_ROOT,
)
from anonymous.engines.ops.kali_ssh import KaliSshTransport

BLOCKED_BINARIES = (
    "hydra",
    "sqlmap",
    "commix",
    "msfconsole",
    "msfvenom",
    "metasploit",
    "hashcat",
    "john",
    "responder",
    "secretsdump",
    "psexec",
    "wmiexec",
    "crackmapexec",
    "impacket",
    "nuclei",
    "nikto",
    "gobuster",
    "ffuf",
    "wfuzz",
    "nmap",
    "masscan",
    "enum4linux",
)


class KaliMcpEngine:
    def __init__(self) -> None:
        self.root = Path(KALI_MCP_ROOT)
        self.compose = self.root / "docker" / "compose.yml"
        self.knowledge_dir = PROJECT_ROOT / "knowledge" / "kali"
        self.sessions_dir = Path(KALI_SESSIONS_DIR)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.configure_backend(
            "docker",
            {"docker": KALI_MCP_URL, "cloud": "", "virtualbox": ""},
        )

    def configure_backend(
        self,
        backend: str,
        mcp_urls: Dict[str, str],
        cloud_ssh: Optional[Dict[str, Any]] = None,
    ) -> None:
        if backend not in ("native", "docker", "cloud", "virtualbox"):
            raise ValueError("El entorno Kali debe ser native, docker, cloud o virtualbox.")
        if not isinstance(mcp_urls, dict):
            raise ValueError("Las URLs MCP deben ser un objeto por entorno.")
        if cloud_ssh is not None and not isinstance(cloud_ssh, dict):
            raise ValueError("La configuración SSH cloud debe ser un objeto.")
        self.backend = backend
        self.mcp_urls = {
            name: mcp_urls.get(name, "").rstrip("/")
            for name in ("docker", "cloud", "virtualbox")
        }
        self.cloud_ssh = dict(cloud_ssh or {})
        self.ssh_transport = KaliSshTransport(self.cloud_ssh)
        self.mcp_url = "" if backend == "cloud" else self.mcp_urls.get(backend, "")

    def _docker_executable(self) -> Optional[str]:
        executable = shutil.which("docker")
        if executable:
            return executable

        candidates = []
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates.append(
                Path(local_app_data) / "Programs" / "DockerDesktop" / "resources" / "bin" / "docker.exe"
            )
        program_files = os.environ.get("ProgramFiles")
        if program_files:
            candidates.append(
                Path(program_files) / "Docker" / "Docker" / "resources" / "bin" / "docker.exe"
            )
        return next((str(candidate) for candidate in candidates if candidate.is_file()), None)

    def _docker_desktop_executable(self) -> Optional[str]:
        candidates = []
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates.append(Path(local_app_data) / "Programs" / "DockerDesktop" / "Docker Desktop.exe")
        program_files = os.environ.get("ProgramFiles")
        if program_files:
            candidates.append(Path(program_files) / "Docker" / "Docker" / "Docker Desktop.exe")
        return next((str(candidate) for candidate in candidates if candidate.is_file()), None)

    def _ensure_docker_daemon(
        self,
        docker: str,
        timeout: int = 60,
        poll_interval: float = 2,
    ) -> Optional[str]:
        """Start Docker Desktop if needed and wait briefly for its engine pipe."""
        def daemon_ready() -> tuple[bool, str]:
            try:
                result = subprocess.run(
                    [docker, "info", "--format", "{{.ServerVersion}}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                return False, str(exc)
            return result.returncode == 0, (result.stderr or "").strip()

        ready, detail = daemon_ready()
        if ready:
            return None

        desktop = self._docker_desktop_executable()
        if not desktop:
            return (
                "El motor de Docker no está disponible y no se encontró Docker Desktop. "
                "Abre Docker Desktop manualmente, espera a que indique que está iniciado "
                "y vuelve a ejecutar `kali start`."
            )

        try:
            subprocess.Popen(
                [desktop],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            return f"No pude iniciar Docker Desktop ({exc}). Ábrelo manualmente y reintenta `kali start`."

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(min(poll_interval, max(0, deadline - time.monotonic())))
            ready, detail = daemon_ready()
            if ready:
                return None

        suffix = f" Detalle: {detail}" if detail else ""
        return (
            f"Docker Desktop se abrió, pero el motor no respondió después de {timeout} segundos."
            f"{suffix} Espera a que Docker Desktop termine de iniciar y vuelve a ejecutar `kali start`."
        )

    def docker_available(self) -> bool:
        return self._docker_executable() is not None

    def status(self) -> Dict[str, Any]:
        docker = self.docker_available()
        compose_exists = self.compose.is_file()
        mcp = self.mcp_health()
        return {
            "docker_installed": docker,
            "backend": self.backend,
            "compose_file": str(self.compose),
            "compose_present": compose_exists,
            "mcp_url": self.mcp_url,
            "connection_type": "SSH" if self.backend == "cloud" else "MCP",
            "connection_target": (
                f"{self.cloud_ssh.get('username', 'kali')}@{self.cloud_ssh.get('host', '')}"
                if self.backend == "cloud"
                else self.mcp_url
            ),
            "mcp_healthy": mcp["healthy"],
            "mcp_detail": mcp["detail"],
            "knowledge_files": len(list(self.knowledge_dir.rglob("*.md"))) if self.knowledge_dir.exists() else 0,
            "active_session": self._active_session_name(),
        }

    def status_text(self, status: Optional[Dict[str, Any]] = None) -> str:
        s = status or self.status()
        lines = [
            "🐉 Integración de Kali",
            f"• Entorno seleccionado: {s['backend']}",
            f"• Docker instalado: {'sí' if s['docker_installed'] else 'no'}",
            f"• compose.yml: {'encontrado' if s['compose_present'] else 'faltante'} ({s['compose_file']})",
            f"• {s['connection_type']}: {s['connection_target'] or 'sin configurar'} → "
            f"{'saludable' if s['mcp_healthy'] else 'caído'} ({s['mcp_detail']})",
            f"• Playbooks locales: {s['knowledge_files']} archivos markdown",
            f"• Sesión activa: {s['active_session'] or 'ninguna'}",
            "",
            "Anonymous no ejecuta Hydra, sqlmap, Metasploit ni auditorías automatizadas.",
            "Kali MCP permite solo descubrimiento Nmap -sn de CIDR privado con confirmación.",
        ]
        return "\n".join(lines)

    def mcp_health(self) -> Dict[str, Any]:
        if self.backend == "cloud":
            return self.ssh_transport.health_check()
        if not self.mcp_url:
            return {
                "healthy": False,
                "detail": f"No hay URL MCP configurada para el entorno `{self.backend}`.",
            }
        try:
            tools, _ = self._mcp_list_tools(timeout=5)
            names = {tool.get("name") for tool in tools}
            if "execute_command" not in names:
                return {
                    "healthy": False,
                    "detail": "MCP responde, pero no expone la herramienta execute_command",
                }
            return {
                "healthy": True,
                "detail": (
                    f"MCP activo; {len(tools)} herramientas, execute_command disponible "
                    "(puede ejecutar comandos dentro del contenedor)"
                ),
            }
        except (OSError, RuntimeError, ValueError, TimeoutError) as exc:
            return {"healthy": False, "detail": str(exc)[:160]}

    def start_stack(self, confirmed: bool = False) -> Dict[str, Any]:
        if not confirmed:
            reason = (
                "Levantar el contenedor Docker Kali MCP (consume RAM)."
                if self.backend == "docker"
                else (
                    "Comprobar la conexión SSH segura con Kali en la nube."
                    if self.backend == "cloud"
                    else f"Comprobar la conexión MCP del entorno `{self.backend}`."
                )
            )
            return self._confirm("kali_start", reason)
        if self.backend != "docker":
            health = self.mcp_health()
            return {
                "ok": health["healthy"],
                "message": (
                    f"Entorno `{self.backend}`: {health['detail']}"
                    if health["healthy"]
                    else f"No se pudo conectar al entorno `{self.backend}`: {health['detail']}"
                ),
            }
        docker = self._docker_executable()
        if not docker:
            return {
                "ok": False,
                "message": "Docker no está en PATH. Instalá Docker Desktop y reintentá `kali start`.",
            }
        if not self.compose.is_file():
            return {"ok": False, "message": f"No encuentro compose.yml en {self.compose}"}
        daemon_error = self._ensure_docker_daemon(docker)
        if daemon_error:
            return {"ok": False, "message": daemon_error}
        proc = subprocess.run(
            [docker, "compose", "-f", str(self.compose), "up", "-d"],
            capture_output=True,
            text=True,
            timeout=180,
        )
        health = self.mcp_health()
        out = (proc.stdout or "")[-800:] + "\n" + (proc.stderr or "")[-400:]
        if proc.returncode != 0:
            return {"ok": False, "message": f"Docker compose falló:\n{out.strip()}"}
        return {
            "ok": True,
            "message": (
                f"Contenedor Kali MCP solicitado.\nMCP {self.mcp_url}: {health['detail']}\n"
                "Primera vez puede tardar minutos en construir la imagen."
            ),
        }

    def stop_stack(self, confirmed: bool = False) -> Dict[str, Any]:
        if not confirmed:
            reason = (
                "Detener el contenedor Docker Kali MCP."
                if self.backend == "docker"
                else f"Detener el entorno `{self.backend}`."
            )
            return self._confirm("kali_stop", reason)
        if self.backend != "docker":
            return {
                "ok": False,
                "message": (
                    f"El entorno `{self.backend}` no se detiene desde Anonymous; "
                    "no se ejecutó ninguna acción."
                ),
            }
        docker = self._docker_executable()
        if not docker or not self.compose.is_file():
            return {"ok": False, "message": "No puedo detener Kali MCP: Docker o compose.yml ausentes."}
        proc = subprocess.run(
            [docker, "compose", "-f", str(self.compose), "down"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            return {"ok": False, "message": (proc.stderr or proc.stdout or "error")[-600:]}
        return {"ok": True, "message": "Contenedor Kali MCP detenido."}

    def start_session(self, target: str, scope: str = "passive") -> Dict[str, Any]:
        target = (target or "127.0.0.1").strip()
        scope_key = scope.lower()
        if scope_key not in ("passive", "passive+creds", "full"):
            scope_key = "passive"
        if scope_key != "passive":
            return {
                "ok": False,
                "message": (
                    "Anonymous solo inicializa sesiones en alcance **passive**. "
                    "Brute force y explotación no se automatizan aquí. Usá el repo kali-mcp-main "
                    "con autorización escrita si necesitás ese flujo."
                ),
            }
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        safe = "".join(ch if ch.isalnum() else "_" for ch in target)
        name = f"{safe}_{stamp}"
        folder = self.sessions_dir / name
        (folder / "assets").mkdir(parents=True, exist_ok=True)
        session_md = (
            f"# Sesión Anonymous / Kali MCP\n\n"
            f"- **Target(s)**: {target}\n"
            f"- **Date**: {datetime.now().isoformat(timespec='seconds')}\n"
            f"- **Scope**: Passive only\n"
            f"- **Status**: IN PROGRESS\n\n"
            f"## Timeline\n- Session initialized\n"
        )
        (folder / "session.md").write_text(session_md, encoding="utf-8")
        (folder / "targets.md").write_text(
            f"# Targets\n\n| Target | Status | Findings |\n|--------|--------|----------|\n| {target} | Pending | — |\n",
            encoding="utf-8",
        )
        (folder / "findings.md").write_text("# Findings\n\n_Todavía vacío._\n", encoding="utf-8")
        self._set_active_session(name)
        return {
            "ok": True,
            "session": name,
            "message": (
                f"SESSION INITIALIZED\nTarget: {target}\nScope: Passive only\nDir: {folder}\n\n"
                "Siguiente: `scan {target}` (motor nativo) o `kali knowledge <tema>`.\n"
                "`kali-audit` automatizado ofensivo no está habilitado en Anonymous."
            ),
        }

    def discover_network(self, target: str, confirmed: bool = False) -> Dict[str, Any]:
        try:
            if not target or "/" not in target:
                raise ValueError("Indicá un CIDR IPv4, por ejemplo `192.168.0.0/24`.")
            network = ipaddress.ip_network(target, strict=False)
            private_networks = (
                ipaddress.ip_network("10.0.0.0/8"),
                ipaddress.ip_network("172.16.0.0/12"),
                ipaddress.ip_network("192.168.0.0/16"),
            )
            if network.version != 4 or not any(network.subnet_of(private) for private in private_networks):
                raise ValueError("Solo se permite descubrir redes IPv4 privadas RFC1918.")
            if network.num_addresses > 256:
                raise ValueError("El alcance máximo permitido es una subred de 256 direcciones (/24).")
        except ValueError as exc:
            return {"ok": False, "message": str(exc)}

        cidr = str(network)
        if not confirmed:
            return {
                "type": "confirmation_required",
                "action": "kali_network_discovery",
                "target": cidr,
                "pending_message": f"kali discover {cidr}",
                "risk_level": "MEDIUM",
                "reason": f"Descubrimiento de hosts en la red privada {cidr} (máximo 256 direcciones).",
                "message": (
                    f"⚠️ Se enviará a Kali {'por SSH' if self.backend == 'cloud' else 'MCP'} "
                    f"un descubrimiento Nmap `-sn` para {cidr}. "
                    "No escanea puertos ni ejecuta pruebas de explotación.\n"
                    "Confirma que tienes autorización para analizar esta red."
                ),
            }

        try:
            if self.backend == "cloud":
                remote_result = self.ssh_transport.discover_network(cidr)
                if not remote_result["ok"]:
                    raise RuntimeError(remote_result["detail"])
                output = remote_result["output"]
            else:
                tools, session_id = self._mcp_list_tools()
                if "execute_command" not in {tool.get("name") for tool in tools}:
                    raise RuntimeError("Kali MCP no expone execute_command; no se envió el escaneo.")
                result, _ = self._mcp_request(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "execute_command",
                            "arguments": {"command": f"nmap -sn -n --reason {cidr}"},
                        },
                    },
                    session_id,
                )
                content = result.get("content", [])
                if not isinstance(content, list):
                    raise RuntimeError("Kali MCP devolvió content con un formato no válido.")
                text_output = "\n".join(
                    item.get("text", "")
                    for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                ).strip()
                if result.get("isError"):
                    raise RuntimeError(text_output or "Kali MCP informó que la llamada falló.")
                structured = result.get("structuredContent")
                command_result = structured.get("result") if isinstance(structured, dict) else None
                if isinstance(command_result, dict):
                    output = "\n".join(
                        value
                        for value in (
                            command_result.get("stdout", ""),
                            command_result.get("stderr", ""),
                        )
                        if isinstance(value, str) and value
                    ).strip()
                    if command_result.get("success") is False:
                        code = command_result.get("return_code", "desconocido")
                        raise RuntimeError(f"nmap terminó con código {code}.\n{output}".strip())
                else:
                    output = text_output
                if not output:
                    output = json.dumps(structured or result, ensure_ascii=False, indent=2)

            artifact = None
            artifact_error = ""
            try:
                artifact = self._save_discovery_output(cidr, output)
            except OSError as exc:
                artifact_error = f"\n\nNo se pudo guardar la evidencia: {exc}"
            interpretation_facts = self._interpret_discovery_output(output)
            transport = "Kali por SSH" if self.backend == "cloud" else "Kali MCP"
            message = f"Descubrimiento de hosts completado por {transport} para {cidr}.\n\n{output}"
            if artifact:
                message += f"\n\nEvidencia guardada en: {artifact}"
            message += artifact_error
            return {
                "ok": True,
                "type": "kali_discovery",
                "target": cidr,
                "output": output,
                "interpretation_facts": interpretation_facts,
                "artifact": str(artifact) if artifact else None,
                "message": message,
            }
        except (OSError, RuntimeError, ValueError, TimeoutError) as exc:
            transport = "Kali por SSH" if self.backend == "cloud" else "Kali MCP"
            return {"ok": False, "message": f"No se pudo ejecutar el descubrimiento en {transport}: {exc}"}

    @staticmethod
    def _interpret_discovery_output(output: str) -> Dict[str, Any]:
        reported_match = re.search(
            r"\((\d+)\s+hosts?\s+up\)",
            output,
            re.IGNORECASE,
        )
        echo_replies = len(re.findall(r"\breceived\s+echo-reply\b", output, re.IGNORECASE))
        tcp_resets = len(re.findall(r"\breceived\s+reset\b", output, re.IGNORECASE))
        return {
            "reported_up": int(reported_match.group(1)) if reported_match else None,
            "confirmed_echo_replies": echo_replies,
            "uncertain_tcp_resets": tcp_resets,
            "warning": (
                "Una respuesta TCP reset puede ser generada por una puerta de enlace o "
                "intermediario; no confirma por sí sola la presencia de un dispositivo."
            ),
        }

    def _mcp_list_tools(self, timeout: int = 120) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        _, session_id = self._mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "anonymous", "version": "1.0"},
                },
            },
            timeout=timeout,
        )
        self._mcp_request(
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            session_id,
            timeout=timeout,
        )
        result, session_id = self._mcp_request(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            session_id,
            timeout=timeout,
        )
        tools = result.get("tools")
        if not isinstance(tools, list):
            raise RuntimeError("Respuesta MCP inválida: tools/list no devolvió una lista de herramientas.")
        return tools, session_id

    def _mcp_request(
        self,
        payload: Dict[str, Any],
        session_id: Optional[str] = None,
        timeout: int = 120,
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if payload.get("method") != "initialize":
            headers["MCP-Protocol-Version"] = "2025-03-26"
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        req = urllib.request.Request(
            self.mcp_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                session_id = response.headers.get("Mcp-Session-Id", session_id)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
            raise RuntimeError(f"MCP HTTP {exc.code}: {detail or exc.reason}") from exc

        if not body.strip():
            return {}, session_id
        messages = self._decode_mcp_messages(body)

        request_id = payload.get("id")
        response_message = next(
            (
                message for message in messages
                if isinstance(message, dict)
                and (request_id is None or message.get("id") == request_id)
            ),
            None,
        )
        if request_id is None:
            return {}, session_id
        if response_message is None:
            raise RuntimeError("MCP no devolvió respuesta al mensaje solicitado.")
        if "error" in response_message:
            error = response_message["error"]
            detail = error.get("message", error) if isinstance(error, dict) else error
            raise RuntimeError(f"MCP respondió con error: {detail}")
        result = response_message.get("result")
        if not isinstance(result, dict):
            raise RuntimeError("MCP devolvió una respuesta JSON-RPC inválida.")
        return result, session_id

    @staticmethod
    def _decode_mcp_messages(body: str) -> List[Any]:
        """Decode JSON or Server-Sent Events returned by Streamable HTTP."""
        normalized = body.replace("\r\n", "\n").strip()
        if normalized.startswith(("event:", "data:")):
            if "\n\n" not in normalized and normalized.endswith("\\n\\n"):
                normalized = normalized[:-4] + "\n\n"
            messages = []
            for block in normalized.split("\n\n"):
                data_lines = [
                    line[5:].lstrip(" ")
                    for line in block.splitlines()
                    if line.startswith("data:")
                ]
                if not data_lines:
                    continue
                data = "\n".join(data_lines)
                if data.strip() == "[DONE]":
                    continue
                try:
                    messages.append(json.loads(data))
                except json.JSONDecodeError as exc:
                    excerpt = data[:200].replace("\n", " ")
                    raise RuntimeError(
                        f"respuesta MCP no válida en evento SSE: {excerpt!r}"
                    ) from exc
            return messages

        try:
            decoded = json.loads(normalized)
        except json.JSONDecodeError as exc:
            excerpt = normalized[:200].replace("\n", " ")
            raise RuntimeError(
                f"respuesta MCP no válida (no es JSON ni SSE): {excerpt!r}"
            ) from exc
        return decoded if isinstance(decoded, list) else [decoded]

    def _save_discovery_output(self, target: str, output: str) -> Optional[Path]:
        name = self._active_session_name()
        if not name:
            return None
        folder = self.sessions_dir / name / "assets"
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        artifact = folder / f"kali_discovery_{stamp}.txt"
        artifact.write_text(f"Target: {target}\n\n{output}\n", encoding="utf-8")
        return artifact

    def finish_session(self) -> Dict[str, Any]:
        name = self._active_session_name()
        if not name:
            return {"ok": False, "message": "No hay sesión Kali activa. Usá `kali-start <objetivo>`."}
        folder = self.sessions_dir / name
        session_file = folder / "session.md"
        if session_file.exists():
            text = session_file.read_text(encoding="utf-8")
            text = text.replace("IN PROGRESS", "FINISHED")
            session_file.write_text(text, encoding="utf-8")
        assets = list((folder / "assets").glob("*")) if (folder / "assets").exists() else []
        self._set_active_session("")
        return {
            "ok": True,
            "message": (
                f"SESSION FINALIZED: {name}\n"
                f"Assets: {len(assets)}\n"
                f"Carpeta: {folder}\n"
                "No se lanzaron herramientas ofensivas desde Anonymous."
            ),
        }

    def search_knowledge(self, query: str, limit: int = 5) -> Dict[str, Any]:
        q = (query or "").strip().lower()
        if not q:
            return {"ok": False, "message": "Indicá un tema, ej: `kali knowledge ssh` o `kali knowledge nmap`."}
        if not self.knowledge_dir.exists():
            return {"ok": False, "message": f"No está la base copiada en {self.knowledge_dir}"}
        scored: List[tuple[int, Path, str]] = []
        terms = [t for t in q.replace(",", " ").split() if len(t) > 2]
        for path in self.knowledge_dir.rglob("*.md"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            blob = f"{path.name} {text}".lower()
            score = sum(3 if term in path.stem.lower() else 1 if term in blob else 0 for term in terms)
            if score:
                scored.append((score, path, text))
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            return {"ok": True, "message": f"Sin playbooks locales para '{query}'."}
        chunks = []
        for score, path, text in scored[:limit]:
            rel = path.relative_to(self.knowledge_dir)
            excerpt = "\n".join(text.splitlines()[:18])
            chunks.append(f"### {rel} (score {score})\n{excerpt}")
        return {"ok": True, "message": "📚 Knowledge Kali MCP (copia local)\n\n" + "\n\n".join(chunks)}

    def refuse_audit(self) -> Dict[str, Any]:
        return {
            "ok": False,
            "message": (
                "`kali-audit` del proyecto original lanza enumeración masiva y, según el alcance, "
                "fuerza bruta o explotación. Anonymous **no copia ese bucle**.\n\n"
                "Flujo permitido acá:\n"
                "1. `kali start` — inicia el contenedor forense (con confirmación); no inicia el MCP opcional\n"
                "2. `kali-start <objetivo>` — carpeta de sesión pasiva\n"
                "3. `scan <objetivo>` / `rag` / `kali knowledge <servicio>`\n"
                "4. `kali-finish`\n\n"
                "`kali discover <CIDR>` requiere que el servicio MCP separado ya esté disponible y confirmación.\n\n"
                "La documentación completa está en la wiki: projects/kali-mcp y wiki/kali-mcp/."
            ),
        }

    def refuse_exec(self, command: str) -> Dict[str, Any]:
        lowered = (command or "").lower()
        for binary in BLOCKED_BINARIES:
            if binary in lowered:
                return {
                    "ok": False,
                    "message": (
                        f"Bloqueado: Anonymous no envía `{binary}` al contenedor Kali. "
                        "Eso sería un procedimiento ofensivo. Usá el motor nativo (`scan`/`ping`) "
                        "o leé `kali knowledge`."
                    ),
                }
        return {
            "ok": False,
            "message": (
                "No hay `execute_command` libre hacia Kali. El MCP queda expuesto en "
                f"{self.mcp_url} para agentes con autorización; Anonymous solo opera el stack y la wiki."
            ),
        }

    def _confirm(self, action: str, reason: str) -> Dict[str, Any]:
        return {
            "type": "confirmation_required",
            "action": action,
            "reason": reason,
            "requires_confirmation": True,
            "ok": False,
            "message": f"⚠️ [AgentShield] {reason}\n¿Autorizar? (S/n)",
        }

    def _active_path(self) -> Path:
        return self.sessions_dir / "active.json"

    def _active_session_name(self) -> str:
        path = self._active_path()
        if not path.exists():
            return ""
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("name") or ""
        except Exception:
            return ""

    def _set_active_session(self, name: str) -> None:
        self._active_path().write_text(json.dumps({"name": name}), encoding="utf-8")


kali_mcp_engine = KaliMcpEngine()
