"""
Gemini Client for Anonymous.
Connects to Google Gemini API (Gemini Flash) with zero external dependency (using urllib.request).
Falls back gracefully to local intelligence mode if GEMINI_API_KEY is not configured yet.
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from anonymous.config import GEMINI_API_KEY, GEMINI_MODEL
from anonymous.brain.prompts import SYSTEM_PROMPT


class GeminiClient:
    """Client for Google Gemini Flash API with built-in fallback."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model: str = GEMINI_MODEL):
        self.api_key = api_key
        self.model = model
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
        """Generates response via Gemini Flash or local intelligent fallback."""
        if not self.is_configured:
            return self._local_fallback_response(prompt)

        endpoint = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

        contents = []
        if history:
            for msg in history:
                role = "user" if msg.get("role") in ("user", "human") else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048,
            }
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=25) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return "Respuesta recibida pero sin contenido textual."
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            return f"[Error Gemini API HTTP {e.code}]: {error_body[:200]}... Usando modo local."
        except Exception as e:
            return f"[Error de Conexión Gemini]: {str(e)}. Usando modo local."

    def _local_fallback_response(self, prompt: str) -> str:
        """Intelligent local responses when API key is not yet set."""
        p_lower = prompt.lower()
        if "scan" in p_lower or "escan" in p_lower or "puerto" in p_lower:
            return (
                "🎯 **Modo Red Team (Auditoría de Red)**\n"
                "Para escanear un objetivo, puedes ejecutar el comando directo:\n"
                "`scan <ip_o_host>` (ej: `scan 127.0.0.1`)\n"
                "Esto activará el escáner nativo multihilo de Python integrado en Anonymous."
            )
        elif "owasp" in p_lower or "mitre" in p_lower or "cis" in p_lower or "rag" in p_lower:
            return (
                "🛡️ **Modo Blue Team (Consulta RAG Normativa)**\n"
                "Puedes consultar la base de conocimiento de seguridad con:\n"
                "`rag <consulta>` (ej: `rag inyeccion sql` o `rag credenciales por defecto`)\n"
                "Consultará instantáneamente la base defensiva local (OWASP Top 10, MITRE, CIS)."
            )
        elif "ptt" in p_lower or "arbol" in p_lower or "tarea" in p_lower:
            return (
                "🌳 **Pentest Task Tree (PTT)**\n"
                "Puedes visualizar el árbol de tareas de auditoría activo usando el comando `ptt`."
            )
        else:
            return (
                "⚡ **Anonymous Core (Modo Local)**\n"
                f"He recibido tu consulta: *\"{prompt}\"*\n\n"
                "Actualmente estoy operando con los motores locales nativos (Escáner de red, RAG normativo, PTT).\n"
                "💡 *Consejo:* Para habilitar el razonamiento en la nube sin límites con Gemini Flash, configura `GEMINI_API_KEY` en tu archivo `.env`."
            )


gemini_client = GeminiClient()
