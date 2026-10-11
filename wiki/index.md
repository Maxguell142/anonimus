---
type: index
title: Catálogo Maestro de la LLM Wiki
created: 2026-10-09
updated: 2026-10-09
tags:
  - wiki-index
  - navigation
---

# Catálogo Maestro de la LLM Wiki (Ecosistema Ciberseguridad & Asistentes)

> **Bienvenido a la LLM Wiki:** Un repositorio persistente de conocimiento compilado e interconectado para explorar en Obsidian o consultar mediante el asistente de IA.

---

## 📂 Proyectos Analizados (`projects/`)

| Página | Resumen y Función Clave | Estado |
| :--- | :--- | :--- |
| **[[projects/pentestgpt\|PentestGPT]]** | Motor de auditoría ofensiva (Red Team) estructurado en el árbol de tareas [[concepts/ptt-task-tree\|PTT]]. | Ingestado |
| **[[projects/cybersecurity-rag\|Cybersecurity RAG]]** | Asistente defensivo (Blue Team) sobre normativas OWASP Top 10, MITRE ATT&CK y CIS Controls. | Ingestado |
| **[[projects/openjarvis\|OpenJarvis]]** | Núcleo orquestador y runtime asíncrono para gestión de agentes, daemons y sesiones. | Ingestado |
| **[[projects/jarvis\|Jarvis]]** | Asistente de escritorio de respuesta rápida con dictado por voz y atajos globales. | Ingestado |
| **[[projects/ecc-agents\|ECC (.agents)]]** | Arnés de contención de seguridad ([[concepts/agentshield-hitl\|AgentShield]]) y optimización de contexto ([[concepts/context-budgeting\|Context Budget]]). | Ingestado |
| **[[projects/anonymous\|Anonymous]]** | **Plataforma híbrida unificada:** Ensambla los 5 proyectos anteriores en una arquitectura nativa sin Docker. | Ingestado / Demo Operativa |

---

## 🧠 Memoria de Configuraciones y Estado (`memory/`)

| Página | Descripción y Parámetros Almacenados |
| :--- | :--- |
| **[[memory/system-config\|Configuración del Sistema]]** | Límites de hardware (8 GB RAM, Ryzen 5), regla No-Docker, puertos (7860) y endpoints. |
| **[[memory/user-preferences\|Preferencias del Usuario]]** | Perfil de Max, idioma español, terminal Warp, tono conciso y políticas de seguridad HITL. |
| **[[memory/mcp-registry\|Registro de Servidores MCP]]** | Plantillas para Google AI Studio MCP, SQLite MCP y Filesystem MCP con sincronización global. |
| **[[memory/active-state\|Memoria de Trabajo Dinámica]]** | Objetivo actual (`127.0.0.1`), fase PTT activa (`Scanning & Enumeration`) y hallazgos recientes. |
| **[[tools/mem\|Herramienta CLI `mem.py`]]** | Utilidad de consola para leer (`get`), alterar (`set-state`) o sincronizar (`sync-mcp`) memoria. |

---

## 🧠 Conceptos y Patrones Clave (`concepts/`)

| Página | Resumen y Principio de Ingeniería |
| :--- | :--- |
| **[[concepts/ptt-task-tree\|Pentesting Task Tree (PTT)]]** | Metodología jerárquica de tareas dependientes para guiar auditorías de penetración paso a paso. |
| **[[concepts/agentshield-hitl\|AgentShield & HITL]]** | Arnés de contención con validación humana interactiva (*Human-In-The-Loop*) antes de ejecutar comandos sensibles. |
| **[[concepts/multiplatform-os\|Multiplataforma Nativa (Sin Docker)]]** | Capa de abstracción `OSAdapter` para correr en Windows 11 y Linux con ahorro masivo de RAM (8 GB target). |
| **[[concepts/rag-vs-wiki\|RAG vs LLM Wiki Persistente]]** | Análisis comparativo entre la recuperación efímera de fragmentos y el compilado acumulativo en Markdown. |
| **[[concepts/context-budgeting\|Presupuesto de Contexto]]** | Técnicas de poda y compresión de historiales y logs para optimizar el consumo de tokens y evitar alucinaciones. |

---

## ⚖️ Comparativas y Síntesis (`comparisons/`)

| Página | Resumen |
| :--- | :--- |
| **[[comparisons/architecture-matrix\|Matriz de Arquitectura]]** | Tabla comparativa global de roles, consumos de RAM, dependencias y mapa de fusión hacia Anonymous. |
| **[[comparisons/agent-runtimes\|Comparativa de Runtimes]]** | Evaluación técnica de los diferentes motores de bucle de control (*Agent Loops*) del ecosistema. |

---

## 🛠️ Gobernanza y Mantenimiento
* **[[SCHEMA\|Guía de Estructura y Reglas (SCHEMA.md)]]**: Directrices para el mantenimiento y evolución de la wiki por parte del LLM.
* **[[log\|Registro Cronológico de Actividad (log.md)]]**: Registro cronológico inmutable de ingestas, consultas y mantenimientos.
