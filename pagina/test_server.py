import io
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from unittest.mock import Mock, patch
from urllib.request import urlopen

from server import (
    TacticalHTTPRequestHandler,
    WEB_CLIENTS,
    WEB_CLIENTS_LOCK,
    get_active_web_clients,
    parse_arp_cache,
    print_devices,
    record_web_client,
    render_live_dashboard,
)


class TacticalHTTPRequestHandlerTests(unittest.TestCase):
    def setUp(self):
        with WEB_CLIENTS_LOCK:
            WEB_CLIENTS.clear()

    def test_client_disconnect_does_not_escape_request_handler(self):
        handler = object.__new__(TacticalHTTPRequestHandler)
        handler.close_connection = False

        with patch.object(
            BaseHTTPRequestHandler,
            "handle_one_request",
            side_effect=ConnectionAbortedError,
        ):
            handler.handle_one_request()

        self.assertTrue(handler.close_connection)

    def test_records_new_and_reconnected_web_clients(self):
        with patch("server.time.time", side_effect=[100, 110, 171]):
            self.assertTrue(record_web_client("192.168.1.20", "Browser"))
            self.assertFalse(record_web_client("192.168.1.20", "Browser"))
            self.assertTrue(record_web_client("192.168.1.20", "Browser"))

    def test_lists_only_recent_web_clients(self):
        with patch("server.time.time", return_value=100):
            record_web_client("192.168.1.20", "Browser")
        with patch("server.time.time", return_value=161):
            self.assertEqual(get_active_web_clients(), [])

    def test_parses_local_arp_cache_entries(self):
        output = (
            "  Interface: 192.168.1.10 --- 0x7\n"
            "  192.168.1.1    aa-bb-cc-dd-ee-ff    dynamic\n"
            "  224.0.0.22     01-00-5e-00-00-16    static\n"
            "  192.168.1.1    aa-bb-cc-dd-ee-ff    dynamic\n"
        )

        self.assertEqual(
            parse_arp_cache(output),
            [{"ip": "192.168.1.1", "mac": "AA:BB:CC:DD:EE:FF"}],
        )

    def test_live_dashboard_shows_web_client_ip(self):
        output = render_live_dashboard(
            "WEP-SER-IP",
            "192.168.1.10",
            8080,
            [{
                "ip": "192.168.1.20",
                "last_seen": "18:00:00",
                "user_agent": "Test Browser",
            }],
            [],
        )

        self.assertIn("WEP-SER-IP", output)
        self.assertIn("IP: 192.168.1.20", output)
        self.assertIn("Actualización automática cada 2 segundos", output)

    def test_opening_web_page_adds_visitor_ip_to_live_list(self):
        httpd = HTTPServer(("127.0.0.1", 0), TacticalHTTPRequestHandler)
        thread = Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{httpd.server_port}/", timeout=3) as response:
                self.assertEqual(response.status, 200)
            clients = get_active_web_clients()
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join()

        self.assertTrue(any(client["ip"] == "127.0.0.1" for client in clients))

    def test_device_inventory_api_is_local_only(self):
        handler = object.__new__(TacticalHTTPRequestHandler)
        handler.path = "/api/devices"
        handler.client_address = ("192.168.1.20", 12345)
        handler.headers = {}
        handler._record_web_visitor = Mock()
        handler._serve_json = Mock()

        handler.do_GET()

        handler._serve_json.assert_called_once_with(
            {"error": "La lista de dispositivos solo está disponible desde este equipo."},
            403,
        )

    def test_terminal_device_command_reads_running_server(self):
        httpd = HTTPServer(("127.0.0.1", 0), TacticalHTTPRequestHandler)
        thread = Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        output = io.StringIO()
        try:
            with patch(
                "server.get_lan_devices",
                return_value=[{"ip": "192.168.1.1", "mac": "AA:BB:CC:DD:EE:FF"}],
            ):
                with redirect_stdout(output):
                    print_devices(httpd.server_port)
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join()

        self.assertIn("Dispositivos conocidos en la red local", output.getvalue())
        self.assertIn("192.168.1.1 | AA:BB:CC:DD:EE:FF", output.getvalue())


if __name__ == "__main__":
    unittest.main()
