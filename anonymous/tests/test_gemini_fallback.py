import sys
import unittest
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.brain.gemini_client import GeminiClient


class TestGeminiFallback(unittest.TestCase):
    def test_unconfigured_uses_local_mode(self):
        client = GeminiClient(api_key="")
        text = client.generate_response("hola mundo")
        self.assertIn("Modo Local", text)

    def test_timeout_falls_back_to_local(self):
        client = GeminiClient(api_key="x" * 20, timeout=1)
        with patch.object(client, "_request_generate", side_effect=TimeoutError("timed out")):
            text = client.generate_response("hola mundo")
        self.assertIn("Modo Local", text)
        self.assertIn("no respondió", text)

    def test_unavailable_primary_uses_supported_fallback_model(self):
        client = GeminiClient(
            api_key="x" * 20,
            model="gemini-3.8-flash",
            fallback_model="gemini-3.6-flash",
        )
        unavailable = urllib.error.HTTPError(
            url="https://example.invalid",
            code=404,
            msg="Model not found",
            hdrs=None,
            fp=BytesIO(b'{"error":"model not found"}'),
        )
        with patch.object(
            client,
            "_request_generate",
            side_effect=[unavailable, "respuesta de respaldo"],
        ) as request:
            text = client.generate_response("hola")

        self.assertEqual(text, "respuesta de respaldo")
        self.assertEqual(
            [call.args[3] for call in request.call_args_list],
            ["gemini-3.8-flash", "gemini-3.6-flash"],
        )

    def test_service_unavailable_retries_primary_then_uses_fallback(self):
        client = GeminiClient(
            api_key="x" * 20,
            model="gemini-3.8-flash",
            fallback_model="gemini-3.6-flash",
        )
        busy = urllib.error.HTTPError(
            url="https://example.invalid",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=BytesIO(b'{"error":"high demand"}'),
        )
        with patch("anonymous.brain.gemini_client.time.sleep"), patch.object(
            client,
            "_request_generate",
            side_effect=[busy, busy, "respuesta de respaldo"],
        ) as request:
            text = client.generate_response("hola")

        self.assertEqual(text, "respuesta de respaldo")
        self.assertEqual(
            [call.args[3] for call in request.call_args_list],
            ["gemini-3.8-flash", "gemini-3.8-flash", "gemini-3.6-flash"],
        )

    def test_does_not_duplicate_last_user_turn(self):
        client = GeminiClient(api_key="x" * 20, timeout=1)
        captured = {}

        def fake_request(prompt, system_instruction, history, model):
            captured["history"] = history
            captured["prompt"] = prompt
            return "ok"

        with patch.object(client, "_request_generate", side_effect=fake_request):
            client.generate_response(
                "hola",
                history=[{"role": "user", "content": "hola"}],
            )
        self.assertEqual(captured["prompt"], "hola")
        self.assertEqual(captured["history"], [])


if __name__ == "__main__":
    unittest.main()
