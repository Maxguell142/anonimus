"""
Configuration management for Anonymous.
Loads environment variables and sets cross-platform paths.
"""

import os
from pathlib import Path

# Load .env file if python-dotenv is present
try:
    from dotenv import load_dotenv
    # Look for .env in project root or current working dir
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass

# Base Directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
USER_DATA_DIR = Path.home() / ".anonymous"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = USER_DATA_DIR / "anonymous.db"

# API Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "20"))

# Server / GUI Settings
SERVER_HOST = os.getenv("ANONYMOUS_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("ANONYMOUS_PORT", "7860"))

# Security Guardrails Settings (ECC AgentShield)
SAFE_MODE = os.getenv("ANONYMOUS_SAFE_MODE", "true").lower() in ("1", "true", "yes")
AUTO_APPROVE_LOW_RISK = True

# Optional Kali MCP (Docker). Default: sibling checkout kali-mcp-main.
KALI_MCP_ROOT = Path(os.getenv("KALI_MCP_ROOT", str(PROJECT_ROOT.parent / "kali-mcp-main")))
KALI_MCP_URL = os.getenv("KALI_MCP_URL", "http://127.0.0.1:666/mcp")
KALI_SESSIONS_DIR = Path(os.getenv("KALI_SESSIONS_DIR", str(USER_DATA_DIR / "kali_sessions")))
