"""
Natural-language intent router for Anonymous.
Maps Spanish/English phrases onto built-in tools before falling through to the LLM.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Optional

_SCAN_VERBS = (
    "scan|escanear|escanea|escaneá|escaneame|escanealo|escanearlo|"
    "revisar|revisa|revisá|verificar|verifica|verificá|"
    "analizar|analiza|analizá"
)
_IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b"
)
_SCAN_VERB_RE = re.compile(rf"\b(?:{_SCAN_VERBS})\b", re.IGNORECASE)
_PING_VERB_RE = re.compile(
    r"\b(ping|est[aá]\s+vivo|responde|conectividad|comprobar conectividad)\b",
    re.IGNORECASE,
)
_QUESTION_RE = re.compile(r"\b(que es|que dice|como|explica|normativa|recomendaciones?)\b", re.IGNORECASE)
_DEFENSIVE_QUESTION_RE = re.compile(
    r"\b(proteger|protege|proteger|prevenir|evitar|mitigar|mitigacion|"
    r"controles?|defender|asegurar|detectar|gestionar|gestion|parches?|"
    r"hardening|recomendaciones?|seguridad)\b",
    re.IGNORECASE,
)
_RAG_HINTS = (
    "owasp",
    "mitre",
    "cis",
    "inyecc",
    "sql",
    "hardening",
    "normativa",
    "mitig",
    "cve",
    "xss",
    "credencial",
    "acceso",
    "escaneo",
    "puerto",
    "api",
    "fuerza bruta",
    "brute force",
    "ssrf",
    "autenticacion",
    "autenticación",
    "parche",
    "registro",
    "eventos",
    "logs",
    "logging",
    "cifrado",
    "criptografia",
    "contraseña",
    "password",
    "phishing",
    "componentes",
    "dependencias",
)
_STOP_HOSTS = {
    "ports",
    "port",
    "puertos",
    "puerto",
    "el",
    "la",
    "los",
    "las",
    "un",
    "una",
    "mi",
    "local",
}


def _extract_target(text: str) -> Optional[str]:
    lower = text.lower()
    if "localhost" in lower:
        return "localhost"
    ip = _IP_RE.search(text)
    if ip:
        return ip.group(0)
    match = re.search(
        rf"\b(?:{_SCAN_VERBS}|ping)\s+(?:los?\s+)?(?:puertos?\s+(?:de|en)\s+)?([a-zA-Z0-9._-]+)",
        lower,
        re.IGNORECASE,
    )
    if match and match.group(1) not in _STOP_HOSTS:
        return match.group(1)
    if any(token in lower for token in ("esta maquina", "esta máquina", "mi pc", "local")):
        return "127.0.0.1"
    return None


def _extract_ports(text: str) -> Optional[str]:
    match = re.search(r"(?:puertos?|ports?)\s*[:=]?\s*([\d,\s]+)", text, re.IGNORECASE)
    if match:
        ports = ",".join(p.strip() for p in match.group(1).split(",") if p.strip().isdigit())
        return ports or None
    match = re.search(
        r"(?:localhost|\b(?:\d{1,3}\.){3}\d{1,3}\b)\s+([\d,\s]+)$",
        text.strip(),
        re.IGNORECASE,
    )
    if match:
        ports = ",".join(p.strip() for p in match.group(1).split(",") if p.strip().isdigit())
        return ports or None
    return None


def parse_intent(text: str) -> Optional[Dict[str, Any]]:
    """Return a tool intent dict, or None to send the text to the LLM."""
    raw = (text or "").strip()
    if not raw:
        return None
    lower = raw.lower()
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", lower)
        if not unicodedata.combining(char)
    )

    if re.search(r"\b(help|ayuda)\b", folded) and len(raw.split()) <= 3:
        return {"action": "help"}

    if re.search(r"\b(ptt|arbol|arbol de tareas|task tree|tareas pendientes)\b", folded):
        if re.search(r"\b(reset|reinici|limpia|borra)\w*\b", folded):
            return {"action": "ptt_reset"}
        return {"action": "ptt"}

    if re.search(r"\b(hallazgos|findings|vulnerabilidades detectadas|puertos abiertos)\b", folded):
        return {"action": "findings"}

    if re.search(r"\b(status|briefing|estado(?: del sistema)?|situacion|resumen operativo)\b", folded):
        return {"action": "status"}

    if re.search(r"\b(reporte|report|informe)\b", folded):
        return {"action": "report"}

    conceptual = bool(_QUESTION_RE.search(folded))
    rag_hint = any(
        "".join(
            char for char in unicodedata.normalize("NFKD", hint)
            if not unicodedata.combining(char)
        ) in folded
        for hint in _RAG_HINTS
    )
    scan_verb = bool(_SCAN_VERB_RE.search(raw))

    if conceptual and rag_hint and not (scan_verb and _extract_target(raw)):
        return {"action": "rag", "query": raw}

    if _DEFENSIVE_QUESTION_RE.search(folded) and rag_hint:
        return {"action": "rag", "query": raw}

    if scan_verb:
        return {
            "action": "scan",
            "target": _extract_target(raw) or "127.0.0.1",
            "ports": _extract_ports(raw),
        }

    if _PING_VERB_RE.search(raw):
        return {"action": "ping", "target": _extract_target(raw) or "127.0.0.1"}

    if folded.startswith("rag ") or folded.startswith("normativa "):
        return {"action": "rag", "query": raw.split(None, 1)[1]}

    if rag_hint and conceptual:
        return {"action": "rag", "query": raw}

    return None
