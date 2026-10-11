#!/usr/bin/env python3
"""
CLI Memory Tool for LLM Wiki (anonimus/wiki).
Allows reading, updating, and syncing configuration and state memories from the terminal.

Usage:
    python mem.py list
    python mem.py get [system|preferences|mcp|state]
    python mem.py set-state <key> <value>
    python mem.py sync-mcp
"""

import sys
import json
import re
from pathlib import Path

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WIKI_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = WIKI_DIR / "memory"
MCP_GLOBAL_CONFIG = Path.home() / ".gemini" / "config" / "mcp_config.json"


def cmd_list():
    print("\n🧠 [Memoria de la Wiki - Archivos de Configuración]:")
    for f in sorted(MEMORY_DIR.glob("*.md")):
        print(f"  • {f.stem:<20} ({f.name})")
    print("")


def cmd_get(name: str):
    target = MEMORY_DIR / f"{name}.md"
    if not target.exists():
        matches = list(MEMORY_DIR.glob(f"*{name}*.md"))
        if matches:
            target = matches[0]
        else:
            print(f"❌ No se encontró archivo de memoria para '{name}'.")
            return

    print(f"\n📖 [Leyendo Memoria: {target.name}]:\n")
    print(target.read_text(encoding="utf-8"))


def cmd_set_state(key: str, value: str):
    state_file = MEMORY_DIR / "active-state.md"
    if not state_file.exists():
        print("❌ active-state.md no existe.")
        return

    content = state_file.read_text(encoding="utf-8")
    pattern = rf"({key}:\s*).*$"
    if re.search(pattern, content, flags=re.MULTILINE):
        new_content = re.sub(pattern, rf"\g<1>\"{value}\"", content, flags=re.MULTILINE)
        state_file.write_text(new_content, encoding="utf-8")
        print(f"✔ Estado actualizado: {key} = \"{value}\" en active-state.md")
    else:
        print(f"⚠️ Clave '{key}' no encontrada en active-state.md.")


def cmd_sync_mcp():
    mcp_file = MEMORY_DIR / "mcp-registry.md"
    if not mcp_file.exists():
        print("❌ mcp-registry.md no existe.")
        return

    MCP_GLOBAL_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    # Default template based on mcp-registry.md
    mcp_config = {
        "mcpServers": {
            "google-ai-studio": {
                "command": "npx",
                "args": ["-y", "aistudio-mcp-server"],
                "env": {
                    "GEMINI_API_KEY": ""
                }
            }
        }
    }
    MCP_GLOBAL_CONFIG.write_text(json.dumps(mcp_config, indent=2), encoding="utf-8")
    print(f"✔ Configuración MCP sincronizada en: {MCP_GLOBAL_CONFIG}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    action = sys.argv[1].lower()
    if action == "list":
        cmd_list()
    elif action == "get":
        name = sys.argv[2] if len(sys.argv) > 2 else "system-config"
        cmd_get(name)
    elif action == "set-state":
        if len(sys.argv) < 4:
            print("Uso: python mem.py set-state <key> <value>")
            return
        cmd_set_state(sys.argv[2], sys.argv[3])
    elif action in ("sync-mcp", "sync"):
        cmd_sync_mcp()
    else:
        print(f"Comando desconocido: '{action}'. Usa 'list', 'get', 'set-state', o 'sync-mcp'.")


if __name__ == "__main__":
    main()
