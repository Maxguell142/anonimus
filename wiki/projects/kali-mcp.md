---
type: project
title: Kali MCP
repo_path: C:\Users\maxgu\Documents\anonimus\kali-mcp-main
tags:
  - project
  - kali
  - mcp
  - docker
created: 2026-10-16
updated: 2026-10-17
---

# Kali MCP — Contenedor Kali + MCP

> **Fuente original:** [`kali-mcp-main`](file:///C:/Users/maxgu/Documents/anonimus/kali-mcp-main)
> **Copia markdown:** [`wiki/kali-mcp/`](file:///C:/Users/maxgu/Documents/anonimus/wiki/kali-mcp) (45 archivos `.md`)
> **Copia runtime:** `anonymous/knowledge/kali/`
> **Rol:** Modo opcional de [[projects/anonymous|Anonymous]]: Docker con Kali Linux y servidor MCP en `http://127.0.0.1:666/mcp`.

---

## 1. Qué hace el proyecto original

Kali MCP conecta agentes de IA con herramientas de Kali vía [Model Context Protocol](https://modelcontextprotocol.io/). El contenedor publica MCP en el puerto **666**. El flujo canónico del repo fuente es:

1. `/kali-start <objetivo>` — sesión y alcance
2. `/kali-audit <objetivo>` — auditoría (sub-agentes)
3. `/kali-finish` — reporte

Documentación ingerida (copias literales):

- [[kali-mcp/README|README]]
- [[kali-mcp/AGENTS|AGENTS.md]] (política de autorización y metodología)
- [[kali-mcp/knowledge/index|knowledge/]] playbooks de herramientas y protocolos
- [[kali-mcp/docs/upstream-issue-healthcheck-500|issue de wrappers HTTP 500]]

---

## 2. Qué hace Anonymous con esto (límite ético)

Anonymous **reutiliza** el stack Docker/MCP y la wiki de conocimiento. **No** automatiza explotación, fuerza bruta ni `execute_command` libre hacia Hydra, sqlmap, Metasploit, commix o nmap del contenedor.

| Capacidad | En kali-mcp-main | En Anonymous |
| :--- | :--- | :--- |
| `docker compose up` del Kali MCP | Sí (`init.sh`) | Sí, `kali start` con HITL |
| Salud MCP `:666/mcp` | Sí | Sí, `kali status` |
| Sesión `sessions/` | Sí | Sí, pasiva en `~/.anonymous/kali_sessions/` |
| `/kali-audit` con explotación | Sí (según alcance) | **Rechazado** (`kali-audit` explica el límite) |
| Consulta de playbooks `.md` | Agente lee knowledge/ | `kali knowledge <tema>` |

---

## 3. Cómo arrancar el contenedor

Requisito: Docker Desktop. Consume RAM extra (la máquina target es de 8 GB: usar este modo solo cuando haga falta).

Desde Anonymous (CLI o escritorio):

```text
kali start          # pide confirmación AgentShield
kali status
kali-start 127.0.0.1
kali knowledge ssh
kali-finish
kali stop
```

O desde el repo fuente:

```bash
cd C:\Users\maxgu\Documents\anonimus\kali-mcp-main
docker compose -f docker/compose.yml up -d
```

Cursor u otro agente puede apuntar a MCP con `anonymous/.mcp.json`:

```json
{ "mcpServers": { "kali": { "type": "http", "url": "http://localhost:666/mcp" } } }
```

---

## 4. Enlaces

* [[commands]] — catálogo de comandos de Anonymous + Kali
* [[projects/anonymous]] — plataforma unificada
* [[memory/mcp-registry]] — registro MCP
* [[memory/system-config]] — Docker ahora es **opcional**, no prohibido
