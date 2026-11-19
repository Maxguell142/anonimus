"""Persistent, non-secret application settings shared by CLI and desktop UI."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlsplit

from anonymous.config import (
    AI_PROVIDER,
    GEMINI_FALLBACK_MODEL,
    GEMINI_MODEL,
    GEMINI_TIMEOUT,
    KALI_MCP_URL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    USER_DATA_DIR,
)

SETTINGS_PATH = USER_DATA_DIR / "settings.json"
KEYRING_SERVICE = "Anonymous"
KEYRING_USERNAME = "gemini-api-key"
BACKENDS = ("native", "docker", "cloud", "virtualbox")
PROVIDERS = ("ollama", "google")
BACKEND_LABELS = {
    "native": "Local (motores integrados)",
    "docker": "Docker (MCP local)",
    "cloud": "Nube (Kali por SSH)",
    "virtualbox": "VirtualBox (MCP)",
}
PROVIDER_LABELS = {
    "ollama": "Ollama",
    "google": "Google Gemini (API)",
}
_SSH_USERNAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{0,31}\Z")
_SSH_HOST_LABEL_PATTERN = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z"
)


class SettingsError(ValueError):
    """Raised when settings cannot be read, validated, or persisted."""


def default_settings() -> Dict[str, Any]:
    return {
        "ai_provider": AI_PROVIDER,
        "ollama_base_url": OLLAMA_BASE_URL,
        "ollama_model": OLLAMA_MODEL,
        "ollama_timeout": OLLAMA_TIMEOUT,
        "gemini_model": GEMINI_MODEL,
        "gemini_fallback_model": GEMINI_FALLBACK_MODEL,
        "gemini_timeout": GEMINI_TIMEOUT,
        "kali_backend": "docker",
        "mcp_urls": {
            "docker": KALI_MCP_URL,
            "cloud": "",
            "virtualbox": "",
        },
        "cloud_ssh": {
            "host": "",
            "username": "kali",
            "port": 22,
            "key_path": "",
            "known_hosts": str(Path.home() / ".ssh" / "known_hosts"),
        },
        "user_name": "",
    }


class SettingsStore:
    """Stores preferences as JSON and API credentials in the OS keyring."""

    def __init__(
        self,
        path: Optional[Path] = None,
        credential_store: Any = None,
    ) -> None:
        self.path = Path(path or SETTINGS_PATH)
        self._credential_store = credential_store

    def load(self) -> Dict[str, Any]:
        defaults = default_settings()
        if not self.path.exists():
            return defaults
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise SettingsError(f"No se pudo leer {self.path}: {exc}") from exc
        return self._normalize(data, defaults)

    def save(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize(settings, default_settings())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(normalized, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
            temporary_path.replace(self.path)
        except OSError as exc:
            raise SettingsError(f"No se pudieron guardar los ajustes en {self.path}: {exc}") from exc
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
        return normalized

    def get_api_key(self) -> str:
        try:
            credentials = self._get_credential_store()
        except SettingsError:
            return os.getenv("GEMINI_API_KEY", "")
        try:
            saved = credentials.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except self._credential_error_types() as exc:
            raise SettingsError(
                f"No se pudo leer la clave de Gemini del almacén del sistema: {exc}"
            ) from exc
        return saved or os.getenv("GEMINI_API_KEY", "")

    def set_api_key(self, api_key: str) -> None:
        credentials = self._get_credential_store()
        try:
            if api_key:
                credentials.set_password(KEYRING_SERVICE, KEYRING_USERNAME, api_key)
            elif credentials.get_password(KEYRING_SERVICE, KEYRING_USERNAME) is not None:
                credentials.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except self._credential_error_types() as exc:
            raise SettingsError(f"No se pudo actualizar la clave de Gemini en el almacén del sistema: {exc}") from exc

    @staticmethod
    def _credential_error_types() -> tuple[type[BaseException], ...]:
        try:
            import keyring.errors
        except ImportError:
            return (OSError, RuntimeError, ValueError)
        return (keyring.errors.KeyringError, OSError, RuntimeError, ValueError)

    def _get_credential_store(self) -> Any:
        if self._credential_store is not None:
            return self._credential_store
        try:
            import keyring
        except ImportError as exc:
            raise SettingsError(
                "Falta el paquete keyring. Instala las dependencias del proyecto para guardar claves."
            ) from exc
        return keyring

    @classmethod
    def _normalize(
        cls,
        settings: Any,
        defaults: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(settings, dict):
            raise SettingsError("El archivo de configuración debe contener un objeto JSON.")
        if "api_key" in settings or "gemini_api_key" in settings:
            raise SettingsError("Las claves API no se guardan en el archivo de ajustes.")
        unknown = set(settings) - set(defaults)
        if unknown:
            raise SettingsError(f"Opciones de configuración desconocidas: {', '.join(sorted(unknown))}.")

        normalized = dict(defaults)
        normalized.update(settings)
        urls = settings.get("mcp_urls", {})
        if not isinstance(urls, dict):
            raise SettingsError("`mcp_urls` debe ser un objeto con URLs por entorno.")
        unknown_urls = set(urls) - {"docker", "cloud", "virtualbox"}
        if unknown_urls:
            raise SettingsError(f"Entornos MCP desconocidos: {', '.join(sorted(unknown_urls))}.")
        normalized["mcp_urls"] = dict(defaults["mcp_urls"])
        normalized["mcp_urls"].update(urls)
        cloud_ssh = settings.get("cloud_ssh", {})
        if not isinstance(cloud_ssh, dict):
            raise SettingsError("`cloud_ssh` debe ser un objeto con los datos de conexión SSH.")
        unknown_ssh = set(cloud_ssh) - set(defaults["cloud_ssh"])
        if unknown_ssh:
            raise SettingsError(f"Opciones SSH desconocidas: {', '.join(sorted(unknown_ssh))}.")
        normalized["cloud_ssh"] = dict(defaults["cloud_ssh"])
        normalized["cloud_ssh"].update(cloud_ssh)

        if not isinstance(normalized["ai_provider"], str) or normalized["ai_provider"] not in PROVIDERS:
            raise SettingsError("El proveedor de IA debe ser `ollama` o `google`.")
        if not isinstance(normalized["kali_backend"], str) or normalized["kali_backend"] not in BACKENDS:
            raise SettingsError("El entorno Kali debe ser `native`, `docker`, `cloud` o `virtualbox`.")
        ssh = normalized["cloud_ssh"]
        host = ssh["host"]
        if not isinstance(host, str) or (host and not cls._valid_ssh_host(host)):
            raise SettingsError("`cloud_ssh.host` debe ser una dirección IPv4 o un nombre de host válido.")
        username = ssh["username"]
        if not isinstance(username, str) or not _SSH_USERNAME_PATTERN.fullmatch(username):
            raise SettingsError("`cloud_ssh.username` debe ser un usuario SSH válido.")
        if type(ssh["port"]) is not int or not 1 <= ssh["port"] <= 65535:
            raise SettingsError("`cloud_ssh.port` debe ser un entero entre 1 y 65535.")
        for field in ("key_path", "known_hosts"):
            value = ssh[field]
            if (
                not isinstance(value, str)
                or len(value) > 4096
                or any(ord(char) < 32 for char in value)
            ):
                raise SettingsError(f"`cloud_ssh.{field}` debe ser una ruta de archivo válida.")
        for field in ("ollama_base_url", "ollama_model", "gemini_model", "gemini_fallback_model"):
            value = normalized[field]
            if not isinstance(value, str) or not value.strip():
                raise SettingsError(f"`{field}` debe ser un texto no vacío.")
        for field, minimum, maximum in (
            ("ollama_timeout", 1, 600),
            ("gemini_timeout", 1, 120),
        ):
            value = normalized[field]
            if type(value) is not int or not minimum <= value <= maximum:
                raise SettingsError(f"`{field}` debe ser un entero entre {minimum} y {maximum}.")

        user_name = normalized["user_name"]
        if (
            not isinstance(user_name, str)
            or len(user_name) > 80
            or any(ord(char) < 32 for char in user_name)
        ):
            raise SettingsError("El nombre visible debe tener hasta 80 caracteres imprimibles.")

        for backend, endpoint in normalized["mcp_urls"].items():
            if not isinstance(endpoint, str):
                raise SettingsError(f"La URL MCP de `{backend}` debe ser texto.")
            if not endpoint:
                continue
            parsed = urlsplit(endpoint)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                raise SettingsError(f"La URL MCP de `{backend}` debe empezar con http:// o https://.")
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise SettingsError(
                    f"La URL MCP de `{backend}` no puede contener credenciales, parámetros ni fragmentos."
                )
            if (
                backend in ("cloud", "virtualbox")
                and parsed.hostname not in ("localhost", "127.0.0.1", "::1")
                and parsed.scheme != "https"
            ):
                raise SettingsError(f"La URL MCP remota de `{backend}` debe usar HTTPS.")
        return normalized

    @staticmethod
    def _valid_ssh_host(host: str) -> bool:
        if not host or len(host) > 253 or host != host.strip():
            return False
        try:
            return ipaddress.ip_address(host).version == 4
        except ValueError:
            return all(_SSH_HOST_LABEL_PATTERN.fullmatch(label) for label in host.split("."))


settings_store = SettingsStore()


def apply_runtime_settings(settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Apply saved preferences to the already-created AI and Kali service clients."""
    configured = settings_store.load() if settings is None else SettingsStore._normalize(
        settings, default_settings()
    )
    api_key = settings_store.get_api_key() if configured["ai_provider"] == "google" else ""

    from anonymous.brain.gemini_client import gemini_client, ollama_client
    from anonymous.engines.ops.kali_mcp import kali_mcp_engine

    gemini_client.configure(
        provider=configured["ai_provider"],
        api_key=api_key,
        model=configured["gemini_model"],
        fallback_model=configured["gemini_fallback_model"],
        timeout=configured["gemini_timeout"],
        ollama_base_url=configured["ollama_base_url"],
        ollama_model=configured["ollama_model"],
        ollama_timeout=configured["ollama_timeout"],
    )
    ollama_client.configure(
        provider="ollama",
        api_key="",
        model=configured["gemini_model"],
        fallback_model=configured["gemini_fallback_model"],
        timeout=configured["gemini_timeout"],
        ollama_base_url=configured["ollama_base_url"],
        ollama_model=configured["ollama_model"],
        ollama_timeout=configured["ollama_timeout"],
    )
    kali_mcp_engine.configure_backend(
        configured["kali_backend"],
        configured["mcp_urls"],
        configured["cloud_ssh"],
    )
    return configured
