"""
Optional Kali MCP / Docker bridge for Anonymous.

Starts the existing kali-mcp-main compose stack, checks MCP health, searches
the copied knowledge markdown, and manages session folders.

Does not run exploit, brute-force, or payload tooling.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from anonymous.config import (
    KALI_MCP_ROOT,
    KALI_MCP_URL,
    KALI_SESSIONS_DIR,
    PROJECT_ROOT,
)

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
        self.mcp_url = KALI_MCP_URL.rstrip("/")
        self.knowledge_dir = PROJECT_ROOT / "knowledge" / "kali"
        self.sessions_dir = Path(KALI_SESSIONS_DIR)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def docker_available(self) -> bool:
        return shutil.which("docker") is not None

    def status(self) -> Dict[str, Any]:
        docker = self.docker_available()
        compose_exists = self.compose.is_file()
        mcp = self.mcp_health()
        return {
            "docker_installed": docker,
            "compose_file": str(self.compose),
            "compose_present": compose_exists,
            "mcp_url": self.mcp_url,
            "mcp_healthy": mcp["healthy"],
            "mcp_detail": mcp["detail"],
            "knowledge_files": len(list(self.knowledge_dir.rglob("*.md"))) if self.knowledge_dir.exists() else 0,
            "active_session": self._active_session_name(),
        }

    def status_text(self) -> str:
        s = self.status()
        lines = [
            "🐉 Kali MCP (modo opcional Docker)",
            f"• Docker instalado: {'sí' if s['docker_installed'] else 'no'}",
            f"• compose.yml: {'encontrado' if s['compose_present'] else 'faltante'} ({s['compose_file']})",
            f"• MCP: {s['mcp_url']} → {'saludable' if s['mcp_healthy'] else 'caído'} ({s['mcp_detail']})",
            f"• Playbooks locales: {s['knowledge_files']} archivos markdown",
            f"• Sesión activa: {s['active_session'] or 'ninguna'}",
            "",
            "Anonymous no ejecuta Hydra, sqlmap, Metasploit, commix ni nmap del contenedor.",
            "Este puente levanta/para el stack, consulta docs y crea sesiones (HITL).",
        ]
        return "\n".join(lines)

    def mcp_health(self) -> Dict[str, Any]:
        try:
            req = urllib.request.Request(self.mcp_url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                code = getattr(resp, "status", 200)
                return {"healthy": code < 500, "detail": f"HTTP {code}"}
        except urllib.error.HTTPError as exc:
            # MCP streamable endpoint often answers 400/406 on a bare GET; server is up.
            if exc.code in (400, 404, 405, 406):
                return {"healthy": True, "detail": f"HTTP {exc.code} (endpoint MCP vivo)"}
            return {"healthy": False, "detail": f"HTTP {exc.code}"}
        except Exception as exc:
            return {"healthy": False, "detail": str(exc)[:160]}

    def start_stack(self, confirmed: bool = False) -> Dict[str, Any]:
        if not confirmed:
            return self._confirm("kali_start", "Levantar el contenedor Docker Kali MCP (consume RAM).")
        if not self.docker_available():
            return {
                "ok": False,
                "message": "Docker no está en PATH. Instalá Docker Desktop y reintentá `kali start`.",
            }
        if not self.compose.is_file():
            return {"ok": False, "message": f"No encuentro compose.yml en {self.compose}"}
        proc = subprocess.run(
            ["docker", "compose", "-f", str(self.compose), "up", "-d"],
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
            return self._confirm("kali_stop", "Detener el contenedor Docker Kali MCP.")
        if not self.docker_available() or not self.compose.is_file():
            return {"ok": False, "message": "No puedo detener Kali MCP: Docker o compose.yml ausentes."}
        proc = subprocess.run(
            ["docker", "compose", "-f", str(self.compose), "down"],
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
                "1. `kali start` — Docker + MCP (con confirmación)\n"
                "2. `kali-start <objetivo>` — carpeta de sesión pasiva\n"
                "3. `scan <objetivo>` / `rag` / `kali knowledge <servicio>`\n"
                "4. `kali-finish`\n\n"
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
