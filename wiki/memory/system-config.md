---
type: memory-config
category: system
title: Configuración del Sistema y Entorno
created: 2026-10-09
updated: 2026-10-17
tags:
  - memory
  - config
  - system
  - hardware
---

# Configuración del Sistema y Entorno (`system-config.md`)

Este archivo actúa como la **memoria persistente de configuraciones técnicas** para el ecosistema de herramientas y el proyecto [[projects/anonymous|Anonymous]]. El agente consulta este archivo para respetar los parámetros del entorno.

---

## 1. Restricciones de Hardware y Plataforma

```yaml
hardware:
  cpu: "AMD Ryzen 5 5500U (6 núcleos, 12 hilos)"
  ram_total_gb: 8
  ram_budget_agent_mb: 300       # Presupuesto máximo asignado al asistente nativo
  docker_enabled: optional       # Kali MCP: docker compose solo bajo demanda (HITL). El núcleo Anonymous sigue nativo.
  os_primary: "Windows 11 Home/Pro (win32)"
  os_secondary: "Linux (Debian/Ubuntu/Kali) compatible"
  terminal_preferred: "Warp Terminal / PowerShell 7"
```

---

## 2. Parámetros de Red y Servidor Local

```yaml
network:
  default_host: "127.0.0.1"
  default_port_gui: 7860          # legado; el HUD actual es Tkinter, no HTTP
  kali_mcp_url: "http://127.0.0.1:666/mcp"
  scan_timeout_seconds: 0.6
  scan_max_workers: 50
  safe_mode_default: true        # Enforce AgentShield HITL
```

---

## 3. Configuración de Modelos e Inteligencia Artificial

```yaml
ai_models:
  primary_cloud_model: "gemini-2.5-flash"
  cloud_provider: "Google AI Studio"
  api_endpoint: "https://generativelanguage.googleapis.com/v1beta"
  context_window_target: "1000000 tokens"
  max_output_tokens: 2048
  temperature_default: 0.3
  fallback_mode: "local-native"  # Si no hay API key, opera con motores locales
```

---

## 4. Rutas Críticas del Ecosistema

```yaml
paths:
  workspace_root: "C:\\Users\\maxgu\\Documents\\anonimus"
  project_anonymous: "C:\\Users\\maxgu\\Documents\\anonimus\\anonymous"
  wiki_vault: "C:\\Users\\maxgu\\Documents\\anonimus\\wiki"
  sqlite_database: "C:\\Users\\maxgu\\.anonymous\\anonymous.db"
  mcp_global_config: "C:\\Users\\maxgu\\.gemini\\config\\mcp_config.json"
  kali_mcp_root: "C:\\Users\\maxgu\\Documents\\anonimus\\kali-mcp-main"
  kali_wiki_copy: "C:\\Users\\maxgu\\Documents\\anonimus\\wiki\\kali-mcp"
  kali_knowledge_copy: "C:\\Users\\maxgu\\Documents\\anonimus\\anonymous\\knowledge\\kali"
```

---

## 5. Historial de Modificaciones

| Fecha | Parámetro | Valor Anterior | Nuevo Valor | Motivo |
| :--- | :--- | :--- | :--- | :--- |
| 2026-10-09 | `docker_enabled` | `null` | `false` | Optimización estricta para 8 GB de RAM. |
| 2026-10-09 | `primary_cloud_model` | `null` | `gemini-2.5-flash` | Modelo gratuito de alta velocidad y 0 MB RAM local. |
| 2026-10-17 | `docker_enabled` | `false` | `optional` | Modo Kali MCP bajo demanda; núcleo sigue nativo por RAM. |
