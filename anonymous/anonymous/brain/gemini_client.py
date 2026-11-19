"""AI client for Anonymous with Ollama and Google Gemini providers."""

import json
import time
import urllib.error
import urllib.request
from typing import List, Dict, Optional
from anonymous.config import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_FALLBACK_MODEL,
    GEMINI_MODEL,
    GEMINI_TIMEOUT,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
)
from anonymous.brain.prompts import KALI_ANALYST_PROMPT, SYSTEM_PROMPT
from anonymous.guardrails.context_budget import context_budget


class GeminiClient:
    """Client for Ollama or Google Gemini with a local fallback."""

    def __init__(
        self,
        api_key: str = GEMINI_API_KEY,
        model: str = GEMINI_MODEL,
        fallback_model: str = GEMINI_FALLBACK_MODEL,
        timeout: int = GEMINI_TIMEOUT,
        provider: Optional[str] = None,
        ollama_base_url: str = OLLAMA_BASE_URL,
        ollama_model: str = OLLAMA_MODEL,
        ollama_timeout: int = OLLAMA_TIMEOUT,
    ):
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.configure(
            provider=provider or AI_PROVIDER,
            api_key=api_key,
            model=model,
            fallback_model=fallback_model,
            timeout=timeout,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model,
            ollama_timeout=ollama_timeout,
        )

    def configure(
        self,
        provider: str,
        api_key: str,
        model: str,
        fallback_model: str,
        timeout: int,
        ollama_base_url: str,
        ollama_model: str,
        ollama_timeout: int,
    ) -> None:
        selected_provider = provider.strip().lower()
        if selected_provider not in ("ollama", "google"):
            raise ValueError("ANONYMOUS_AI_PROVIDER debe ser 'ollama' o 'google'.")
        self.provider = selected_provider
        self.api_key = api_key
        self.model = model
        self.fallback_model = fallback_model
        self.timeout = timeout
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.ollama_model = ollama_model
        self.ollama_timeout = ollama_timeout

    @property
    def is_configured(self) -> bool:
        if self.provider == "ollama":
            return bool(self.ollama_base_url and self.ollama_model)
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
        response, last_error = self._generate_remote_response(prompt, system_instruction, pruned)
        if response:
            return response

        local = self._local_fallback_response(prompt)
        hint = (
            f"\n\n_({self.provider.title()} no respondió a tiempo o falló: "
            f"{last_error[:120]}. Respuesta local.)_"
        )
        return local + hint

    def interpret_network_discovery(
        self,
        target: str,
        facts: Dict[str, object],
    ) -> Optional[str]:
        return self.answer_kali_question(
            "Resume el resultado del descubrimiento de hosts e indica qué conclusiones "
            "pueden y no pueden obtenerse.",
            target,
            facts,
        )

    def answer_kali_question(
        self,
        question: str,
        target: Optional[str],
        facts: Optional[Dict[str, object]],
    ) -> Optional[str]:
        if not self.is_configured:
            return None
        prompt = (
            f"Pregunta del usuario: {question}\n"
            f"Alcance autorizado: {target or 'no especificado'}\n"
            "Datos estructurados disponibles:\n"
            f"{json.dumps(facts or {}, ensure_ascii=False, sort_keys=True)}"
        )
        response, _ = self._generate_remote_response(
            prompt,
            KALI_ANALYST_PROMPT,
            [],
        )
        return response or None

    def _generate_remote_response(
        self,
        prompt: str,
        system_instruction: str,
        history: List[Dict[str, str]],
    ) -> tuple[str, str]:
        if self.provider == "ollama":
            try:
                response = self._request_ollama(prompt, system_instruction, history)
                return (response, "") if response else ("", "Ollama devolvió una respuesta vacía.")
            except Exception as exc:
                return "", str(exc)

        models = []
        for name in (self.model, self.fallback_model):
            if name and name not in models:
                models.append(name)

        last_error = ""
        for model in models:
            for _attempt in range(2):
                try:
                    text = self._request_generate(prompt, system_instruction, history, model)
                    if text:
                        return text, last_error
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

        return "", last_error

    def _request_ollama(
        self,
        prompt: str,
        system_instruction: str,
        history: List[Dict[str, str]],
    ) -> str:
        messages = [{"role": "system", "content": system_instruction}]
        for msg in history:
            role = "assistant" if msg.get("role") in ("assistant", "model") else "user"
            messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 2048},
        }
        req = urllib.request.Request(
            f"{self.ollama_base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.ollama_timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result.get("message", {}).get("content", "") or ""

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


gemini_client = GeminiClient(provider=AI_PROVIDER)
ollama_client = GeminiClient(provider="ollama")
