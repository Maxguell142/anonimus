import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.brain.gemini_client import GeminiClient


class TestAIProvider(unittest.TestCase):
    def test_ollama_is_available_as_a_provider_without_google_key(self):
        client = GeminiClient(
            api_key="",
            provider="ollama",
            ollama_base_url="http://localhost:11434",
            ollama_model="qwen2.5:3b",
        )

        self.assertTrue(client.is_configured)
        self.assertEqual(client.provider, "ollama")
        self.assertEqual(client.ollama_model, "qwen2.5:3b")

    def test_ollama_response_uses_chat_api_with_model_and_conversation(self):
        client = GeminiClient(
            api_key="",
            provider="ollama",
            ollama_base_url="http://localhost:11434",
            ollama_model="qwen2.5:3b",
        )
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"message": {"content": "Respuesta de Ollama"}}
        ).encode("utf-8")

        with patch("anonymous.brain.gemini_client.urllib.request.urlopen", return_value=response) as urlopen:
            result = client._request_ollama(
                "pregunta actual",
                "instrucción del sistema",
                [{"role": "user", "content": "pregunta anterior"}],
            )

        self.assertEqual(result, "Respuesta de Ollama")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/api/chat")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "qwen2.5:3b")
        self.assertFalse(payload["stream"])
        self.assertEqual(
            payload["messages"],
            [
                {"role": "system", "content": "instrucción del sistema"},
                {"role": "user", "content": "pregunta anterior"},
                {"role": "user", "content": "pregunta actual"},
            ],
        )

    def test_selected_ollama_provider_generates_response_without_google_key(self):
        client = GeminiClient(api_key="", provider="ollama")
        with patch.object(client, "_request_ollama", return_value="Respuesta local"):
            result = client.generate_response("hola")

        self.assertEqual(result, "Respuesta local")

    def test_kali_question_is_sent_to_ollama_with_only_structured_facts(self):
        client = GeminiClient(api_key="", provider="ollama")
        captured = {}

        def fake_request(prompt, system_instruction, history):
            captured["prompt"] = prompt
            captured["system_instruction"] = system_instruction
            return "No es posible deducir vulnerabilidades del descubrimiento."

        facts = {"reported_up": 4, "confirmed_echo_replies": 2}
        with patch.object(client, "_request_ollama", side_effect=fake_request) as request:
            answer = client.answer_kali_question(
                "¿Qué equipos son más vulnerables?",
                "192.168.0.0/24",
                facts,
            )

        self.assertIn("192.168.0.0/24", captured["prompt"])
        self.assertIn('"reported_up": 4', captured["prompt"])
        self.assertIn("¿Qué equipos son más vulnerables?", captured["prompt"])
        self.assertIn("no inventes", captured["system_instruction"].lower())
        self.assertIn("comandos arbitrarios", captured["system_instruction"].lower())
        request.assert_called_once()
        self.assertEqual(
            answer,
            "No es posible deducir vulnerabilidades del descubrimiento.",
        )

    def test_unavailable_ollama_reports_error_and_uses_local_fallback(self):
        client = GeminiClient(api_key="", provider="ollama")
        with patch.object(client, "_request_ollama", side_effect=TimeoutError("timed out")):
            result = client.generate_response("hola")

        self.assertIn("Modo Local", result)
        self.assertIn("Ollama", result)
        self.assertIn("timed out", result)


if __name__ == "__main__":
    unittest.main()
