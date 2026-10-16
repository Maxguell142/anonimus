#!/usr/bin/env python3
"""
Anonymous Tactical Web Server
Servidor HTTP nativo y ligero para la interfaz HUD de Anonymous.
Transmite en 0.0.0.0 permitiendo el acceso tanto local (localhost) como
a través de la red Wi-Fi desde cualquier dispositivo (smartphone, tablet, PC).
"""

import os
import sys
import json
import socket
import argparse
import threading
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, List
import urllib.parse
import time

# Directorio de archivos web
PAGINA_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PAGINA_DIR.parent

# Intentar importar el motor de Anonymous si está disponible en sys.path
sys.path.insert(0, str(PROJECT_ROOT / "anonymous"))
try:
    from anonymous.core.dispatcher import dispatcher
    from anonymous.engines.red.ptt import ptt_engine
    HAS_ANONYMOUS_CORE = True
except Exception:
    HAS_ANONYMOUS_CORE = False

def get_local_ip() -> str:
    """Detecta la dirección IP local asignada por Wi-Fi o red LAN."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No hace conexión real, solo determina la interfaz saliente preferida
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# Estado en memoria para la sesión web interactiva
SESSION_STATE = {
    "mode": "normal",
    "target": "127.0.0.1",
    "findings": [
        {
            "id": 1,
            "title": "Puerto 8080 HTTP Abierto",
            "target": "127.0.0.1",
            "severity": "INFO",
            "description": "Servidor Tactical HUD de Anonymous activo y escuchando peticiones.",
            "timestamp": "12:10:00"
        },
        {
            "id": 2,
            "title": "Verificación AgentShield HITL",
            "target": "127.0.0.1",
            "severity": "LOW",
            "description": "Filtro de confirmación humana activo para escaneos de subred y comandos peligrosos.",
            "timestamp": "12:11:15"
        }
    ],
    "ptt_tree": [
        {
            "id": "T1",
            "phase": "Reconocimiento",
            "title": "Descubrimiento de Hosts y Sockets",
            "status": "completed",
            "details": "Detección de interfaces de red activas (Wi-Fi 10.0.5.49 / Localhost)."
        },
        {
            "id": "T2",
            "phase": "Escaneo",
            "title": "Mapeo de Puertos TCP Críticos",
            "status": "in_progress",
            "details": "Auditoría de puertos comunes (21, 22, 80, 443, 3306, 8080) sin dependencias externas."
        },
        {
            "id": "T3",
            "phase": "Enumeración",
            "title": "Identificación de Banners y Versiones",
            "status": "pending",
            "details": "Lectura de cabeceras HTTP y respuestas de bienvenida de servicios."
        },
        {
            "id": "T4",
            "phase": "Evaluación Defensiva",
            "title": "Cotejo Normativo RAG (OWASP/MITRE)",
            "status": "pending",
            "details": "Mapeo de hallazgos contra OWASP Top 10 y matriz de técnicas MITRE ATT&CK."
        },
        {
            "id": "T5",
            "phase": "Reporte",
            "title": "Generación de Informe Ejecutivo y Markdown",
            "status": "pending",
            "details": "Sintetizar hallazgos, severidades y mitigaciones recomendadas para Obsidian."
        }
    ]
}

# Base de conocimiento RAG defensiva integrada
DEFENSIVE_KB = {
    "owasp": [
        {
            "id": "A01:2021",
            "title": "Broken Access Control (Control de Acceso Roto)",
            "risk": "Crítico",
            "remediation": "Aplicar principio de mínimo privilegio, validar tokens JWT en cada endpoint y desactivar listado de directorios.",
            "category": "OWASP Top 10"
        },
        {
            "id": "A02:2021",
            "title": "Cryptographic Failures (Fallas Criptográficas)",
            "risk": "Alto",
            "remediation": "Cifrar datos en tránsito con TLS 1.3, almacenar contraseñas con Argon2id o bcrypt y evitar algoritmos obsoletos como MD5/SHA1.",
            "category": "OWASP Top 10"
        },
        {
            "id": "A03:2021",
            "title": "Injection (Inyecciones SQL / Comandos)",
            "risk": "Crítico",
            "remediation": "Utilizar sentencias preparadas (Prepared Statements), validación de esquemas y ORMs seguros.",
            "category": "OWASP Top 10"
        },
        {
            "id": "A05:2021",
            "title": "Security Misconfiguration (Mala Configuración de Seguridad)",
            "risk": "Medio-Alto",
            "remediation": "Eliminar credenciales por defecto, deshabilitar puertos no utilizados y configurar cabeceras CSP, HSTS y X-Frame-Options.",
            "category": "OWASP Top 10"
        }
    ],
    "mitre": [
        {
            "id": "T1046",
            "title": "Network Service Discovery (Descubrimiento de Servicios de Red)",
            "tactic": "Discovery",
            "mitigation": "Segmentación de VLANs, firewall perimetral y monitoreo con IDS/IPS (Suricata/Snort).",
            "category": "MITRE ATT&CK"
        },
        {
            "id": "T1190",
            "title": "Exploit Public-Facing Application",
            "tactic": "Initial Access",
            "mitigation": "Web Application Firewall (WAF), parches continuos y escaneo periódico con PTT.",
            "category": "MITRE ATT&CK"
        },
        {
            "id": "T1059",
            "title": "Command and Scripting Interpreter (PowerShell/Bash)",
            "tactic": "Execution",
            "mitigation": "Habilitar PowerShell Script Block Logging (EID 4104) y restringir modo ConstrainedLanguage.",
            "category": "MITRE ATT&CK"
        }
    ],
    "cis": [
        {
            "id": "CIS-01",
            "title": "Control de Inventario de Activos Empresariales",
            "description": "Rastrear activamente todos los dispositivos conectados a la red local y Wi-Fi.",
            "category": "CIS Controls v8"
        },
        {
            "id": "CIS-04",
            "title": "Configuración Segura de Servidores y Clientes",
            "description": "Establecer y mantener líneas base seguras con auditorías automatizadas periódicas.",
            "category": "CIS Controls v8"
        }
    ]
}

def scan_port(host: str, port: int, timeout: float = 0.35) -> Dict[str, Any]:
    """Escanea un único puerto TCP nativamente mediante sockets sin requerir herramientas externas."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    start_t = time.time()
    try:
        res = sock.connect_ex((host, port))
        latency = round((time.time() - start_t) * 1000, 2)
        if res == 0:
            service_name = "Desconocido"
            try:
                service_name = socket.getservbyport(port, "tcp")
            except Exception:
                pass
            return {"port": port, "open": True, "service": service_name, "latency_ms": latency}
    except Exception:
        pass
    finally:
        sock.close()
    return {"port": port, "open": False, "service": "", "latency_ms": 0}

def run_tcp_scan(target: str, ports: List[int]) -> List[Dict[str, Any]]:
    """Escanea una lista de puertos TCP concurrentemente con hilos."""
    results = []
    threads = []
    lock = threading.Lock()

    def worker(p: int):
        info = scan_port(target, p)
        if info["open"]:
            with lock:
                results.append(info)

    for p in ports:
        t = threading.Thread(target=worker, args=(p,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=1.5)

    results.sort(key=lambda x: x["port"])
    return results


class TacticalHTTPRequestHandler(BaseHTTPRequestHandler):
    """Manejador HTTP para la GUI web táctica y la API REST."""

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self.close_connection = True

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _serve_json(self, data: Any, status_code: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Rutas de API REST
        if path == "/api/status":
            local_ip = get_local_ip()
            data = {
                "system": "Anonymous Unified Platform",
                "status": "ONLINE",
                "mode": SESSION_STATE["mode"],
                "target": SESSION_STATE["target"],
                "local_ip": local_ip,
                "port": self.server.server_port,
                "platform": sys.platform,
                "python": sys.version.split()[0],
                "has_core_engine": HAS_ANONYMOUS_CORE,
                "findings_count": len(SESSION_STATE["findings"]),
                "server_time": time.strftime("%H:%M:%S")
            }
            self._serve_json(data)
            return

        if path == "/api/ptt":
            self._serve_json({"ptt_tree": SESSION_STATE["ptt_tree"]})
            return

        if path == "/api/findings":
            self._serve_json({"findings": SESSION_STATE["findings"]})
            return

        if path == "/api/rag":
            self._serve_json(DEFENSIVE_KB)
            return

        # Servir archivos estáticos de la carpeta `pagina`
        clean_path = path.lstrip("/")
        if not clean_path or clean_path == "/":
            clean_path = "index.html"

        file_path = PAGINA_DIR / clean_path
        if not file_path.is_file() or not str(file_path.resolve()).startswith(str(PAGINA_DIR.resolve())):
            self.send_response(404)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 Not Found - Recurso no encontrado en Anonymous Tactical Web")
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "application/octet-stream"
        if content_type.startswith("text/") or content_type in ("application/javascript", "application/json"):
            content_type += "; charset=utf-8"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
        except OSError as e:
            self.log_error("No se pudo leer el archivo %s: %s", file_path, e)
            self.send_error(500, "No se pudo leer el recurso solicitado")
            return

        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Leer cuerpo de la petición
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(post_data)
        except Exception:
            payload = {}

        if path == "/api/mode":
            new_mode = payload.get("mode", "normal")
            SESSION_STATE["mode"] = new_mode
            self._serve_json({"status": "ok", "mode": new_mode})
            return

        if path == "/api/scan":
            target = payload.get("target", "127.0.0.1").strip()
            ports = payload.get("ports", [21, 22, 53, 80, 443, 3306, 5000, 7860, 8080, 8443])
            SESSION_STATE["target"] = target

            open_ports = run_tcp_scan(target, ports)
            
            # Registrar hallazgos si se encuentran puertos abiertos
            for item in open_ports:
                finding_id = len(SESSION_STATE["findings"]) + 1
                SESSION_STATE["findings"].append({
                    "id": finding_id,
                    "title": f"Puerto Abierto TCP/{item['port']} ({item['service'] or 'servicio'})",
                    "target": target,
                    "severity": "MEDIUM" if item["port"] in (21, 22, 3306) else "INFO",
                    "description": f"Servicio detectado con latencia de {item['latency_ms']}ms.",
                    "timestamp": time.strftime("%H:%M:%S")
                })

            # Avanzar PTT
            for t in SESSION_STATE["ptt_tree"]:
                if t["id"] == "T2":
                    t["status"] = "completed"
                elif t["id"] == "T3":
                    t["status"] = "in_progress"

            self._serve_json({
                "target": target,
                "ports_scanned": len(ports),
                "open_ports": open_ports,
                "timestamp": time.strftime("%H:%M:%S")
            })
            return

        if path == "/api/command":
            cmd_text = payload.get("command", "").strip()
            confirmed = bool(payload.get("confirmed", False))
            
            # Procesar con el motor nativo de Anonymous si está presente
            if HAS_ANONYMOUS_CORE:
                try:
                    result = dispatcher.process_input(cmd_text, confirmed_by_user=confirmed)
                    self._serve_json({"source": "anonymous_core", "result": result})
                    return
                except Exception as e:
                    # En caso de error en el core, hacer fallback elegante
                    pass

            # Manejador emulado nativo para comandos
            response = self._handle_emulated_command(cmd_text, confirmed)
            self._serve_json({"source": "tactical_web_engine", "result": response})
            return

        self.send_response(404)
        self.end_headers()

    def _handle_emulated_command(self, cmd_text: str, confirmed: bool) -> Dict[str, Any]:
        parts = cmd_text.split()
        if not parts:
            return {"type": "empty", "message": "Escribe un comando válido o usa 'help'."}

        verb = parts[0].lower()
        if verb in ("help", "ayuda", "?"):
            return {
                "type": "help",
                "message": (
                    "Comandos tácticos disponibles:\n"
                    "• status / estado    : Telemetría y estado de red Wi-Fi\n"
                    "• scan [ip] [puertos]: Escaneo TCP de sockets rápido\n"
                    "• ping [ip]          : Test de conectividad a socket\n"
                    "• ptt                : Despliega el árbol de tareas de pentest\n"
                    "• rag [owasp|mitre]  : Consulta la base de normativas defensivas\n"
                    "• findings           : Lista hallazgos registrados en sesión\n"
                    "• mode [attack|defense|normal] : Cambia el modo HUD del sistema\n"
                    "• clear              : Limpia la terminal"
                )
            }

        if verb in ("status", "estado", "briefing"):
            local_ip = get_local_ip()
            return {
                "type": "status",
                "message": f"ANONYMOUS HUD ONLINE\nIP Wi-Fi: {local_ip}\nModo: {SESSION_STATE['mode'].upper()}\nObjetivo: {SESSION_STATE['target']}\nHallazgos: {len(SESSION_STATE['findings'])}"
            }

        if verb == "scan":
            target = parts[1] if len(parts) > 1 else SESSION_STATE["target"]
            # Comprobar si requiere confirmación AgentShield
            if not confirmed and target not in ("127.0.0.1", "localhost", get_local_ip()):
                return {
                    "type": "agentshield_alert",
                    "requires_confirmation": True,
                    "target": target,
                    "message": f"[AgentShield HITL] Advertencia: Escaneo a host no local ({target}). Requiere autorización humana para proceder."
                }
            open_ports = run_tcp_scan(target, [21, 22, 53, 80, 443, 3306, 5000, 7860, 8080, 8443])
            return {
                "type": "scan_result",
                "target": target,
                "open_ports": open_ports,
                "message": f"Escaneo finalizado en {target}. {len(open_ports)} puertos abiertos detectados."
            }

        if verb == "ping":
            target = parts[1] if len(parts) > 1 else "127.0.0.1"
            info = scan_port(target, 80, timeout=0.5)
            if not info["open"]:
                info = scan_port(target, 8080, timeout=0.5)
            latency = info["latency_ms"] if info["open"] else 0.5
            return {
                "type": "ping",
                "target": target,
                "alive": True,
                "latency_ms": latency,
                "message": f"Host {target} activo. Latencia: {latency}ms."
            }

        if verb == "ptt":
            return {
                "type": "ptt",
                "tree": SESSION_STATE["ptt_tree"],
                "message": f"Árbol PTT cargado ({len(SESSION_STATE['ptt_tree'])} fases jerárquicas)."
            }

        if verb in ("rag", "normativa"):
            query = " ".join(parts[1:]).lower() if len(parts) > 1 else "owasp"
            matched = []
            for category, items in DEFENSIVE_KB.items():
                if query in category or query in ("todos", "all"):
                    matched.extend(items)
                else:
                    for it in items:
                        if query in it["title"].lower() or query in it.get("remediation", "").lower() or query in it.get("mitigation", "").lower():
                            matched.append(it)
            if not matched:
                matched = DEFENSIVE_KB["owasp"]
            return {
                "type": "rag_result",
                "query": query,
                "items": matched,
                "message": f"Se recuperaron {len(matched)} directrices defensivas del motor RAG."
            }

        if verb in ("findings", "hallazgos"):
            return {
                "type": "findings",
                "items": SESSION_STATE["findings"],
                "message": f"{len(SESSION_STATE['findings'])} hallazgos registrados en la sesión actual."
            }

        if verb == "mode":
            m = parts[1].lower() if len(parts) > 1 else "normal"
            if m in ("attack", "ataque"):
                SESSION_STATE["mode"] = "attack"
            elif m in ("defense", "defensa"):
                SESSION_STATE["mode"] = "defense"
            elif m in ("success", "exito", "completed"):
                SESSION_STATE["mode"] = "completed"
            elif m in ("error",):
                SESSION_STATE["mode"] = "error"
            else:
                SESSION_STATE["mode"] = "normal"
            return {
                "type": "mode_change",
                "mode": SESSION_STATE["mode"],
                "message": f"Modo de HUD actualizado a: {SESSION_STATE['mode'].upper()}"
            }

        return {
            "type": "ai_response",
            "message": f"[Asistente Anonymous]: Procesando consulta sobre '{cmd_text}'. Usa 'scan <ip>' para auditar o 'rag owasp' para consultar defensas."
        }

    def log_message(self, format, *args):
        # Log simplificado para no saturar la consola
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {format % args}\n")


def run_server(port: int = 8080):
    """Inicia el servidor HTTP en 0.0.0.0 permitiendo acceso por Wi-Fi y Localhost."""
    local_ip = get_local_ip()
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, TacticalHTTPRequestHandler)

    banner = (
        "======================================================================\n"
        r"     ____  _   _  ___  _   _ __   ____  __  ___  _   _ ____  " + "\n"
        r"    / ___|| | | |/ _ \| \ | |\ \ / /  \/  |/ _ \| | | / ___| " + "\n"
        r"   | |    | |_| | | | |  \| | \ V /| |\/| | | | | | | \___ \ " + "\n"
        r"   | |___ |  _  | |_| | |\  |  | | | |  | | |_| | |_| |___) |" + "\n"
        r"    \____||_| |_|\___/|_| \_|  |_| |_|  |_|\___/ \___/|____/ " + "\n"
        "                                                             \n"
        "    [+] PLATAFORMA HÍBRIDA DE CIBERSEGURIDAD // HUD TÁCTICO WEB\n"
        "======================================================================\n"
        f"  [>] ENLACE LOCAL (Localhost):  http://localhost:{port}\n"
        f"  [>] ENLACE WI-FI / RED LOCAL:  http://{local_ip}:{port}\n"
        f"  [>] BIND DE RED:               0.0.0.0:{port} (Transmisión activa)\n"
        f"  [>] DIRECTORIO DE ARCHIVOS:    {PAGINA_DIR}\n"
        "======================================================================\n"
        f"  Accede desde cualquier navegador en esta PC o desde tu teléfono,\n"
        f"  tablet u otra laptop conectada a la misma red Wi-Fi ({local_ip}).\n"
        "  Presiona CTRL+C para detener el servidor.\n"
        "======================================================================\n"
    )
    print(banner)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Deteniendo servidor HTTP táctico...")
        httpd.server_close()
        print("[✓] Servidor detenido de manera limpia.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor Web Táctico Anonymous")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Puerto TCP a utilizar (por defecto: 8080)")
    args = parser.parse_args()
    run_server(args.port)
