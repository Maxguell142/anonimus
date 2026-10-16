import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler

from server import TacticalHTTPRequestHandler


class TacticalHTTPRequestHandlerTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
