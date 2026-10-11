"""
Web Server for Anonymous GUI.
Pure Python zero-dependency HTTP server with REST API and static UI serving.
"""

import json
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any

from anonymous.config import SERVER_HOST, SERVER_PORT
from anonymous.core.dispatcher import dispatcher
from anonymous.engines.ops.briefing import briefing_engine
from anonymous.engines.red.ptt import ptt_engine
from anonymous.core.session import session_manager

STATIC_DIR = Path(__file__).resolve().parent / "ui" / "web"


class AnonymousHTTPHandler(SimpleHTTPRequestHandler):
    """Handles static web requests and REST API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/status":
            briefing = briefing_engine.get_briefing()
            self._send_json_response(briefing)
        elif self.path == "/api/ptt":
            tasks = ptt_engine.get_all_tasks()
            self._send_json_response({"tasks": tasks})
        elif self.path == "/api/findings":
            findings = session_manager.get_findings()
            self._send_json_response({"findings": findings})
        elif self.path in ("/", "/index.html"):
            self.path = "/index.html"
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path in ("/api/chat", "/api/command"):
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(raw_body) if raw_body else {}
                msg = payload.get("message", "")
                result = dispatcher.process_input(msg)
                self._send_json_response(result)
            except Exception as e:
                self._send_json_response({"type": "error", "message": str(e)}, status_code=500)
        else:
            self._send_json_response({"error": "Endpoint no encontrado"}, status_code=404)

    def log_message(self, format, *args):
        # Quiet logger for clean console
        pass


def run_server(host: str = SERVER_HOST, port: int = SERVER_PORT, open_browser: bool = True):
    """Starts the Web GUI server."""
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, AnonymousHTTPHandler)
    url = f"http://{host}:{port}"
    print(f"\n[Anonymous GUI] Servidor activo en: {url}")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Anonymous GUI] Deteniendo servidor...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
