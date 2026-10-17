---
type: memory-config
category: mcp
title: Registro y Configuraciones de Servidores MCP
created: 2026-10-09
updated: 2026-10-09
tags:
  - memory
  - mcp
  - google-ai-studio
  - integrations
---

# Registro y Configuraciones de Servidores MCP (`mcp-registry.md`)

Este archivo almacena las **plantillas y configuraciones de servidores MCP (Model Context Protocol)** disponibles para conectar con el asistente de Antigravity y la plataforma [[projects/anonymous|Anonymous]].

---

## 1. Servidor Principal: Google AI Studio MCP

Conecta el asistente con las herramientas y APIs multimodales de Google AI Studio.

### Especificación de Configuración:
```json
{
  "google-ai-studio": {
    "command": "npx",
    "args": ["-y", "aistudio-mcp-server"],
    "env": {
      "GEMINI_API_KEY": "${GEMINI_API_KEY}"
    },
    "description": "Acceso a Gemini 2.0/1.5 Flash para procesamiento de documentos, video y audio",
    "status": "ready-to-activate"
  }
}
```

* **Paquete npm:** `aistudio-mcp-server`
* **Transporte:** Stdio (local vía Node.js / npx)
* **Requisito:** Clave `GEMINI_API_KEY` válida configurada en variables de entorno o archivo `.env`.

---

## 2. Servidores MCP Auxiliares Disponibles

### A. SQLite MCP (Consulta directa a la base de datos de Anonymous)
```json
{
  "anonymous-sqlite": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-sqlite",
      "--db-path",
      "C:\\Users\\maxgu\\.anonymous\\anonymous.db"
    ],
    "description": "Permite inspeccionar directamente las tablas de findings y tareas PTT",
    "status": "available"
  }
}
```

### B. Filesystem MCP (Acceso seguro a proyectos de trabajo)
```json
{
  "anonimus-filesystem": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-filesystem",
      "C:\\Users\\maxgu\\Documents\\anonimus"
    ],
    "description": "Acceso indexado a los repositorios del ecosistema",
    "status": "available"
  }
}
```

### C. Kali MCP (contenedor Docker)
```json
{
  "kali": {
    "type": "http",
    "url": "http://localhost:666/mcp",
    "description": "Kali Linux tools via MCP. Arrancar con `kali start` en Anonymous o docker compose en kali-mcp-main.",
    "status": "optional-docker"
  }
}
```

* **Archivo de proyecto:** `anonymous/.mcp.json`
* **Compose:** `kali-mcp-main/docker/compose.yml` (puerto anfitrión 666 → 8000)
* **En Anonymous:** el agente unificado no llama wrappers ofensivos; solo stack, salud, knowledge y sesiones pasivas. Ver [[projects/kali-mcp]] y [[commands]].

---

## 3. Protocolo de Sincronización con Antigravity

Para aplicar cualquier cambio de este registro a Antigravity globalmente:
1. El archivo destino es: [`C:\Users\maxgu\.gemini\config\mcp_config.json`](file:///C:/Users/maxgu/.gemini/config/mcp_config.json).
2. El agente copia las entradas del bloque `mcpServers` a ese archivo.
3. Al reiniciar la sesión o recargar herramientas, Antigravity monta los nuevos comandos.
