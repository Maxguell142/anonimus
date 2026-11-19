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
    "analizar|analiza|analizá|analisa"
)
_IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b"
)
_CIDR_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d?\d)/(?:[0-9]|[12]\d|3[0-2])\b"
)
_SCAN_VERB_RE = re.compile(rf"\b(?:{_SCAN_VERBS})\b", re.IGNORECASE)
_SCAN_NOUN_RE = re.compile(r"\b(escaneo|scan)\b", re.IGNORECASE)
_NETWORK_SCOPE_RE = re.compile(r"\b(red|subred|network|lan|cidr)\b", re.IGNORECASE)
_KALI_CAPABILITIES_RE = re.compile(
    r"\b(que\s+(?:podes|puedes|puedo)\s+hacer|que\s+herramientas|"
    r"capacidades|opciones)\b",
    re.IGNORECASE,
)
_KALI_UNSCOPED_ACTION_RE = re.compile(
    r"\b(realiz\w*|realis\w*|ejecut\w*|lanz\w*)\b.{0,32}\b(en|con)\s+kali\b",
    re.IGNORECASE,
)
_AMBIGUOUS_OPTION_RE = re.compile(
    r"\b(primera|segunda|tercera|cuarta|\d{1,2})\s+op\w*\b",
    re.IGNORECASE,
)
_OFFENSIVE_OPERATION_RE = re.compile(
    r"\b(ataqu\w*|taqu\w*|explot\w*|vulnerabil\w*|vuln)\b",
    re.IGNORECASE,
)
_OPERATION_VERB_RE = re.compile(
    r"\b(inici\w*|empez\w*|realiz\w*|realis\w*|relis\w*|ejecut\w*|lanz\w*|"
    r"hac\w*|escane\w*|proba\w*|corr\w*|usa\w*)\b",
    re.IGNORECASE,
)
_UNKNOWN_DEVICE_RE = re.compile(
    r"\b(dispositivos?\s+(?:desconocidos?|no\s+identificados?)|"
    r"equipos?\s+(?:desconocidos?|no\s+identificados?))\b",
    re.IGNORECASE,
)
_CONNECTED_DEVICE_RE = re.compile(
    r"\b(equip\w*|dispositiv\w*|hosts?)\b.{0,24}\bconect\w*\b",
    re.IGNORECASE,
)
_DEVICE_COUNT_RE = re.compile(
    r"\b(cuant\w*|numero\s+de)\s+(?:equip\w*|dispositiv\w*|hosts?)\b",
    re.IGNORECASE,
)
_NETWORK_EXPLANATION_RE = re.compile(
    r"\b(que es|que significa|explica|definicion)\b",
    re.IGNORECASE,
)
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
    "vos",
    "tu",
    "tú",
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

    if re.search(r"\b(help|ayuda|comandos)\b", folded) and len(raw.split()) <= 3:
        return {"action": "help"}

    if (
        _AMBIGUOUS_OPTION_RE.search(folded)
        and _OPERATION_VERB_RE.search(folded)
    ):
        return {"action": "kali_capabilities"}

    if "kali" in folded and (
        _KALI_CAPABILITIES_RE.search(folded)
        or _KALI_UNSCOPED_ACTION_RE.search(folded)
    ):
        return {"action": "kali_capabilities"}

    if (
        _OFFENSIVE_OPERATION_RE.search(folded)
        and _OPERATION_VERB_RE.search(folded)
    ):
        return {"action": "kali_unsupported_operation"}

    if re.search(r"\bkali-audit\b", folded) or "auditoria kali" in folded or "auditoría kali" in folded:
        return {"action": "kali_audit"}
    if re.search(r"\bkali-finish\b", folded) or "cerrar sesion kali" in folded or "cerrar sesión kali" in folded:
        return {"action": "kali_finish"}
    if re.search(r"\bkali-start\b", folded) or re.search(r"\bsesion kali\b", folded) or re.search(r"\bsesión kali\b", folded):
        return {"action": "kali_session_start", "target": _extract_target(raw) or "127.0.0.1"}
    if re.search(r"\b(playbook|knowledge kali|docs kali)\b", folded) or (
        "kali" in folded and any(w in folded for w in ("playbook", "knowledge", "documentacion", "documentación"))
    ):
        query = raw
        for prefix in ("kali knowledge", "playbook", "docs kali"):
            if folded.startswith(prefix):
                query = raw.split(None, 2)[-1] if len(raw.split()) > 2 else raw
                break
        return {"action": "kali_knowledge", "query": query}
    kali_start_request = (
        "kali" in folded
        and re.search(r"\b(levant\w*|inici\w*|inisi\w*|arranc\w*|conect\w*)\b", folded)
        and not re.search(r"\b(escane\w*|scan|discover|descubrimiento)\b", folded)
    )
    if (
        kali_start_request
        or re.search(r"\b(levant(a|á|ar) kali|iniciar kali|kali start|docker kali)\b", folded)
    ):
        return {"action": "kali_start_stack"}
    if re.search(r"\b(parar kali|detener kali|kali stop)\b", folded):
        return {"action": "kali_stop_stack"}
    if re.search(r"\b(estado de kali|kali status|salud kali|mcp kali)\b", folded):
        return {"action": "kali_status"}

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
    scan_noun = bool(_SCAN_NOUN_RE.search(folded))
    cidr = _CIDR_RE.search(raw)
    scan_for_user = bool(
        scan_verb and re.search(r"\b(?:vos|por\s+vos)\b", folded)
    )
    if scan_for_user:
        return {
            "action": "kali_network_discovery",
            "target": None,
            "local_network": True,
        }

    kali_scan_request = (
        "kali" in folded
        and scan_noun
        and re.search(r"\b(iniciar|empezar|hacer|realizar)\b", folded)
    )
    unknown_device_request = bool(
        _UNKNOWN_DEVICE_RE.search(folded) and _NETWORK_SCOPE_RE.search(folded)
    )
    connected_device_request = bool(_CONNECTED_DEVICE_RE.search(folded))
    network_device_count = bool(
        _NETWORK_SCOPE_RE.search(folded) and _DEVICE_COUNT_RE.search(folded)
    )
    router_request = bool(
        re.search(r"\b(?:mi|mio|propio|propia)\s+(?:router|ruter|enrutador)\b", folded)
        or re.search(r"\bde\s+mi\s+(?:router|ruter|enrutador)\b", folded)
    )
    network_scan = (
        ((scan_verb or scan_noun) and (_NETWORK_SCOPE_RE.search(folded) or cidr))
        or kali_scan_request
        or unknown_device_request
        or network_device_count
        or connected_device_request
        or router_request
    )

    if network_scan and not _NETWORK_EXPLANATION_RE.search(folded):
        return {
            "action": "kali_network_discovery",
            "target": cidr.group(0) if cidr else None,
            "local_network": bool(
                re.search(r"\bmi\b.{0,24}\b(?:red|router|ruter|enrutador)\b", folded)
            ),
        }

    vulnerability_ranking = bool(
        re.search(r"\b(vulnerab\w*|bulnerab\w*)\b", folded)
        and re.search(
            r"\b(cual\w*|que\s+(?:equip\w*|dispositiv\w*|host\w*)|"
            r"mas\s+(?:vulnerab\w*|bulnerab\w*))\b",
            folded,
        )
    )
    if vulnerability_ranking:
        return {"action": "vulnerability_summary", "query": raw}

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
