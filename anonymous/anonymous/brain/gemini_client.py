"""
Gemini Client for Anonymous.
Connects to Google Gemini API with urllib, retries, model fallback, and a real local fallback.
"""

import json
import time
import urllib.error
import urllib.request
from typing import List, Dict, Optional
from anonymous.config import GEMINI_API_KEY, GEMINI_FALLBACK_MODEL, GEMINI_MODEL, GEMINI_TIMEOUT
from anonymous.brain.prompts import SYSTEM_PROMPT
from anonymous.guardrails.context_budget import context_budget


class GeminiClient:
    """Client for Google Gemini API with retries and local fallback."""

    def __init__(
        self,
        api_key: str = GEMINI_API_KEY,
        model: str = GEMINI_MODEL,
        fallback_model: str = GEMINI_FALLBACK_MODEL,
        timeout: int = GEMINI_TIMEOUT,
    ):
        self.api_key = api_key
        self.model = model
        self.fallback_model = fallback_model
        self.timeout = timeout
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def generate_response(
        self,
        prompt: str,
        system_instruction: str = SYSTEM_PROMPT,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        if not self.is_configured:
            return self._local_fallback_response(prompt)

        pruned = context_budget.prune_history(list(history or []))
        if (
            pruned
            and pruned[-1].get("content") == prompt
            and pruned[-1].get("role") in ("user", "human")
        ):
            pruned = pruned[:-1]
        models = []
        for name in (self.model, self.fallback_model):
            if name and name not in models:
                models.append(name)

        last_error = ""
        for model in models:
            for _attempt in range(2):
                try:
                    text = self._request_generate(prompt, system_instruction, pruned, model)
                    if text:
                        return text
                except urllib.error.HTTPError as exc:
                    body = exc.read().decode("utf-8", errors="ignore")[:180]
                    last_error = f"HTTP {exc.code}: {body}"
                    retryable = exc.code == 429 or 500 <= exc.code < 600
                    if retryable and _attempt < 1:
                        time.sleep(0.5 * (2 ** _attempt))
                        continue
                    break
                except Exception as exc:
                    last_error = str(exc)
                    continue

        local = self._local_fallback_response(prompt)
        hint = f"\n\n_(Gemini no respondió a tiempo o falló: {last_error[:120]}. Respuesta local.)_"
        return local + hint

    def _request_generate(
        self,
        prompt: str,
        system_instruction: str,
        history: List[Dict[str, str]],
        model: str,
    ) -> str:
        endpoint = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
        contents = []
        for msg in history:
            role = "user" if msg.get("role") in ("user", "human") else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        candidates = result.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return ""
        return parts[0].get("text", "") or ""

    def _local_fallback_response(self, prompt: str) -> str:
        p_lower = prompt.lower()
        if "scan" in p_lower or "escan" in p_lower or "puerto" in p_lower:
            return (
                "🎯 **Modo Red Team (Auditoría de Red)**\n"
                "Para escanear un objetivo, ejecuta:\n"
                "`scan <ip_o_host>` o en lenguaje natural: `escaneá localhost`."
            )
        if "owasp" in p_lower or "mitre" in p_lower or "cis" in p_lower or "rag" in p_lower:
            return (
                "🛡️ **Modo Blue Team (Consulta RAG Normativa)**\n"
                "Usa `rag <consulta>` o pregunta p. ej. `qué dice OWASP sobre inyección SQL`."
            )
        if "ptt" in p_lower or "arbol" in p_lower or "árbol" in p_lower or "tarea" in p_lower:
            return "🌳 **Pentest Task Tree (PTT)**\nUsa el comando `ptt` para ver el árbol de tareas."
        return (
            "⚡ **Anonymous Core (Modo Local)**\n"
            f"He recibido tu consulta: *\"{prompt}\"*\n\n"
            "Estoy operando con motores locales (escáner, RAG normativo, PTT).\n"
            "Comandos: `scan`, `rag`, `ptt`, `status`, o frases en español equivalentes."
        )


gemini_client = GeminiClient()
