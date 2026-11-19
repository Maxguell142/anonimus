"""Restricted, read-only forensic operations against the local Kali container."""

from __future__ import annotations

import os
import re
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Dict, Optional, Sequence

from anonymous.config import (
    KALI_EVIDENCE_DIR,
    KALI_FORENSICS_CONTAINER,
    KALI_RESULTS_DIR,
)
from anonymous.engines.ops.kali_mcp import KaliMcpEngine

MAX_OUTPUT_CHARS = 20_000
READ_ONLY_OPERATIONS = {
    "identify": ("file",),
    "metadata": ("exiftool",),
    "hash": ("sha256sum", "md5sum"),
    "partitions": ("mmls",),
    "ewf-info": ("ewfinfo",),
    "ewf-verify": ("ewfverify",),
    "files": ("fls",),
    "binwalk": ("binwalk",),
}


class KaliForensicsEngine:
    def __init__(self) -> None:
        self.container = KALI_FORENSICS_CONTAINER
        self.evidence_dir = Path(KALI_EVIDENCE_DIR)
        self.results_dir = Path(KALI_RESULTS_DIR)
        self._docker = KaliMcpEngine()

    def _docker_environment(self, executable: str) -> Dict[str, str]:
        environment = os.environ.copy()
        docker_dir = str(Path(executable).resolve().parent)
        path_entries = environment.get("PATH", "").split(os.pathsep)
        if docker_dir.casefold() not in {entry.casefold() for entry in path_entries}:
            environment["PATH"] = os.pathsep.join(
                [docker_dir, *[entry for entry in path_entries if entry]]
            )
        return environment

    def _run_docker(self, args: Sequence[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
        executable = self._docker._docker_executable()
        if not executable:
            raise RuntimeError("No encuentro Docker Desktop. Inicia Docker Desktop y vuelve a intentarlo.")
        process = subprocess.Popen(
            [executable, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self._docker_environment(executable),
        )
        captured: Dict[str, bytes] = {}
        truncated: Dict[str, bool] = {}
        reader_errors: list[OSError] = []

        def drain_stream(name: str, stream: BinaryIO) -> None:
            output = bytearray()
            was_truncated = False
            try:
                while True:
                    chunk = stream.read(8192)
                    if not chunk:
                        break
                    remaining = MAX_OUTPUT_CHARS - len(output)
                    if remaining > 0:
                        output.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        was_truncated = True
            except OSError as exc:
                reader_errors.append(exc)
            captured[name] = bytes(output)
            truncated[name] = was_truncated

        readers = [
            threading.Thread(target=drain_stream, args=("stdout", process.stdout)),
            threading.Thread(target=drain_stream, args=("stderr", process.stderr)),
        ]
        for reader in readers:
            reader.start()
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            for reader in readers:
                reader.join()
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
            raise
        for reader in readers:
            reader.join()
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()
        if reader_errors:
            raise reader_errors[0]

        def decode(name: str) -> str:
            value = captured[name].decode("utf-8", errors="replace")
            if truncated[name]:
                value += "\n[Salida truncada por el límite de seguridad.]"
            return value

        return subprocess.CompletedProcess(
            args=[executable, *args],
            returncode=returncode,
            stdout=decode("stdout"),
            stderr=decode("stderr"),
        )

    def _expected_evidence_mount_sources(self) -> set[str]:
        host_path = self.evidence_dir.resolve().as_posix().casefold().rstrip("/")
        sources = {host_path}
        windows_drive = re.match(r"^([a-z]):/(.*)$", host_path)
        if windows_drive:
            drive, path = windows_drive.groups()
            sources.update(
                {
                    f"/run/desktop/mnt/host/{drive}/{path}",
                    f"/host_mnt/{drive}/{path}",
                }
            )
        return sources

    def status(self) -> Dict[str, str | bool]:
        try:
            result = self._run_docker(
                [
                    "inspect",
                    "--format",
                    (
                        '{{.State.Status}}|{{range .Mounts}}{{if eq .Destination '
                        '"/evidencias"}}{{.Source}}|{{.RW}}{{end}}{{end}}'
                    ),
                    self.container,
                ]
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return {
                "connected": False,
                "evidence_read_only": False,
                "container": self.container,
                "state": "unknown",
                "detail": str(exc)[:240],
            }
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()
            return {
                "connected": False,
                "evidence_read_only": False,
                "container": self.container,
                "state": (
                    "missing"
                    if "no such object" in detail.lower() or "no such container" in detail.lower()
                    else "unknown"
                ),
                "detail": detail[:240] or "Docker no pudo inspeccionar el contenedor.",
            }
        state, _, mount_status = result.stdout.strip().partition("|")
        source, separator, read_write = mount_status.partition("|")
        source = source.replace("\\", "/").casefold().rstrip("/")
        evidence_read_only = bool(
            separator
            and source in self._expected_evidence_mount_sources()
            and read_write.strip().lower() == "false"
        )
        if not source:
            detail = "La carpeta Evidencias no está montada en /evidencias."
        elif source not in self._expected_evidence_mount_sources():
            detail = "El montaje /evidencias no apunta a la carpeta Evidencias configurada."
        elif read_write.strip().lower() != "false":
            detail = "La carpeta Evidencias no está montada en solo lectura."
        else:
            detail = "Contenedor forense accesible; Evidencias está montada en solo lectura."
        return {
            "connected": state == "running" and evidence_read_only,
            "evidence_read_only": evidence_read_only,
            "container": self.container,
            "state": state,
            "detail": detail if state == "running" else f"El contenedor está {state or 'en estado desconocido'}. {detail}",
        }

    def start_container(self, confirmed: bool = False) -> Dict[str, object]:
        if not confirmed:
            return {
                "type": "confirmation_required",
                "action": "kali_forensics_start",
                "pending_message": "kali start",
                "reason": "Iniciar el contenedor Kali forense (consume memoria y CPU).",
                "message": "¿Iniciar el contenedor Kali forense ya configurado?",
            }
        executable = self._docker._docker_executable()
        if not executable:
            return {"ok": False, "message": "No encuentro Docker Desktop."}
        daemon_error = self._docker._ensure_docker_daemon(executable)
        if daemon_error:
            return {"ok": False, "message": daemon_error}
        current = self.status()
        if current["state"] == "missing":
            return {
                "ok": False,
                "message": (
                    f"No existe el contenedor `{self.container}`. Revisa Docker Desktop; "
                    "no voy a crear otro contenedor con montajes distintos automáticamente."
                ),
            }
        if not current["evidence_read_only"]:
            return {
                "ok": False,
                "message": (
                    "No iniciaré Kali porque no pude verificar que Evidencias apunte a la "
                    f"carpeta configurada y esté montada en solo lectura. {current['detail']}"
                ),
            }
        if current["connected"]:
            return {"ok": True, "message": f"El contenedor `{self.container}` ya está iniciado."}
        try:
            result = self._run_docker(["start", self.container])
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            return {"ok": False, "message": f"No se pudo iniciar Kali: {exc}"}
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()
            return {"ok": False, "message": f"Docker no pudo iniciar Kali: {detail[:400]}"}
        verified = self.status()
        if not verified["connected"]:
            return {
                "ok": False,
                "message": f"Docker inició el contenedor, pero su estado es {verified['state']}.",
            }
        return {"ok": True, "message": f"Kali forense `{self.container}` iniciado."}

    def stop_container(self, confirmed: bool = False) -> Dict[str, object]:
        if not confirmed:
            return {
                "type": "confirmation_required",
                "action": "kali_forensics_stop",
                "pending_message": "kali stop",
                "reason": "Detener el contenedor Kali forense.",
                "message": "¿Detener el contenedor Kali forense?",
            }
        executable = self._docker._docker_executable()
        if not executable:
            return {"ok": False, "message": "No encuentro Docker Desktop."}
        daemon_error = self._docker._ensure_docker_daemon(executable)
        if daemon_error:
            return {"ok": False, "message": daemon_error}
        current = self.status()
        if current["state"] == "missing":
            return {"ok": False, "message": f"No existe el contenedor `{self.container}`."}
        if current["state"] != "running":
            return {"ok": True, "message": f"El contenedor `{self.container}` ya está detenido."}
        try:
            result = self._run_docker(["stop", "--timeout", "10", self.container], timeout=20)
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            return {"ok": False, "message": f"No se pudo detener Kali: {exc}"}
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()
            return {"ok": False, "message": f"Docker no pudo detener Kali: {detail[:400]}"}
        return {"ok": True, "message": f"Kali forense `{self.container}` detenido."}

    @staticmethod
    def _validate_filename(filename: str) -> str:
        name = (filename or "").strip()
        if (
            not name
            or name in {".", ".."}
            or name.startswith("-")
            or "/" in name
            or "\\" in name
            or any(ord(char) < 32 for char in name)
        ):
            raise ValueError(
                "Indica solo el nombre de un archivo directamente dentro de Evidencias; "
                "no se aceptan rutas, opciones ni comandos."
            )
        return name

    def _evidence_path(self, filename: str) -> tuple[Path, str]:
        name = self._validate_filename(filename)
        root = self.evidence_dir.resolve(strict=True)
        evidence = (root / name).resolve(strict=True)
        if evidence.parent != root or not evidence.is_file():
            raise ValueError("El archivo debe ser un archivo regular dentro de Evidencias.")
        return evidence, f"/evidencias/{name}"

    def _invoke(self, operation: str, container_path: str, timeout: int = 120) -> str:
        commands = READ_ONLY_OPERATIONS.get(operation)
        if not commands:
            raise ValueError(f"Operación forense no permitida: {operation}.")

        outputs = []
        for command in commands:
            args = ["exec", self.container, command]
            if operation == "identify":
                args.extend(["--", container_path])
            elif operation == "metadata":
                args.extend(["-s", "-FileName", "-FileType", "-MIMEType", "-FileSize", container_path])
            elif operation == "hash":
                args.extend(["--", container_path])
            elif operation == "partitions":
                args.append(container_path)
            elif operation in {"ewf-info", "ewf-verify"}:
                args.append(container_path)
            elif operation == "files":
                args.extend(["-p", container_path])
            elif operation == "binwalk":
                args.append(container_path)
            result = self._run_docker(args, timeout=timeout)
            text = (result.stdout or "").strip()
            error = (result.stderr or "").strip()
            if result.returncode:
                detail = error or text or f"{command} terminó con código {result.returncode}."
                raise RuntimeError(detail[:MAX_OUTPUT_CHARS])
            if operation == "hash":
                outputs.append(text)
            elif text:
                outputs.append(text)
            if error:
                outputs.append(error)
        return "\n\n".join(outputs)[:MAX_OUTPUT_CHARS]

    def analyze(self, operation: str, filename: str) -> Dict[str, object]:
        operation = (operation or "").strip().lower()
        if operation not in READ_ONLY_OPERATIONS:
            return {
                "ok": False,
                "message": (
                    "Operación no disponible. Usa `kali forensic tools` para ver las "
                    "consultas forenses integradas."
                ),
            }

        status = self.status()
        if not status["connected"] or not status["evidence_read_only"]:
            return {
                "ok": False,
                "message": (
                    f"No se puede conectar al contenedor `{self.container}` "
                    f"(estado: {status['state']}). {status['detail']}"
                ),
            }

        try:
            _, container_path = self._evidence_path(filename)
            if operation.startswith("ewf-") and not re.search(
                r"\.(?:e\d{2}|ex\d{2})$", filename, re.IGNORECASE
            ):
                raise ValueError("ewf-info y ewf-verify requieren una evidencia EWF, por ejemplo archivo.E01.")
            output = self._invoke(
                operation,
                container_path,
                timeout=300 if operation == "ewf-verify" else 120,
            )
            report_path: Optional[Path] = None
            if operation == "hash":
                self.results_dir.mkdir(parents=True, exist_ok=True)
                safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name)[:80]
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                report_path = self.results_dir / f"{safe_name}.{stamp}.hashes.txt"
                with report_path.open("x", encoding="utf-8", newline="\n") as report:
                    report.write(f"Evidence: {filename}\n{output}\n")
            message = f"Kali forensics · {operation} · {filename}\n\n{output}"
            if report_path:
                message += f"\n\nHashes guardados en: {report_path}"
            return {
                "ok": True,
                "operation": operation,
                "filename": filename,
                "output": output,
                "report": str(report_path) if report_path else None,
                "message": message,
            }
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            return {"ok": False, "message": f"No se pudo analizar la evidencia: {exc}"}

    def tools_text(self) -> str:
        tools = "\n".join(
            f"• {operation}: {', '.join(commands)}"
            for operation, commands in READ_ONLY_OPERATIONS.items()
        )
        return (
            f"Contenedor: {self.container}\n"
            f"Evidencias (solo lectura): {self.evidence_dir}\n"
            f"Resultados: {self.results_dir}\n"
            "Consultas integradas de solo lectura:\n"
            f"{tools}\n"
            "No se admiten comandos arbitrarios, herramientas que escriban en Evidencias, "
            "ni operaciones de ataque."
        )


kali_forensics_engine = KaliForensicsEngine()
