# Registro Cronológico de la Wiki (Log)

Registro inmutable de operaciones de ingesta, consultas y salud sobre la base de conocimiento persistente.

---

## [2026-10-09] init | Inicialización de la Wiki y Definición de SCHEMA
- Creada la infraestructura base del repositorio de la wiki en `C:\Users\maxgu\Documents\anonimus\wiki`.
- Creado [[SCHEMA.md]] con las reglas de gobierno, taxonomía y protocolos de ingesta/consulta.

## [2026-10-09] ingest | PentestGPT-main
- Analizado el código fuente de `PentestGPT-main`.
- Creada página [[projects/pentestgpt]].
- Extraídos conceptos clave: Árbol de Tareas PTT, análisis de fases y parser de consola.
- Creada página conceptual [[concepts/ptt-task-tree]].

## [2026-10-09] ingest | cybersecurity-rag-assistant-main
- Analizado el código fuente de `cybersecurity-rag-assistant-main`.
- Creada página [[projects/cybersecurity-rag]].
- Evaluadas normativas integradas (OWASP Top 10, MITRE ATT&CK, CIS Controls) y pipeline de ChromaDB.
- Creada página conceptual de contraste [[concepts/rag-vs-wiki]].

## [2026-10-09] ingest | OpenJarvis-main
- Analizado el repositorio `OpenJarvis-main`.
- Creada página [[projects/openjarvis]].
- Documentado el runtime asíncrono, orquestador de eventos, soporte MCP y arquitectura de sesiones.

## [2026-10-09] ingest | jarvis-main
- Analizado el repositorio `jarvis-main`.
- Creada página [[projects/jarvis]].
- Documentados los módulos de dictado por voz, atajos globales y empaquetado para escritorio Windows.

## [2026-10-09] ingest | ECC (.agents)
- Analizado el arnés de gobernanza y habilidades de `.agents`.
- Creada página [[projects/ecc-agents]].
- Documentadas las reglas de seguridad, clasificador de riesgo y contención.
- Creada página conceptual [[concepts/agentshield-hitl]] y [[concepts/context-budgeting]].

## [2026-10-09] ingest | Anonymous (Fusión Unificada)
- Creada página [[projects/anonymous]] documentando la integración de los 5 proyectos.
- Creada página conceptual [[concepts/multiplatform-os]] detallando la ejecución nativa en Windows y Linux sin Docker.
- Generada la síntesis en [[comparisons/architecture-matrix]] y [[comparisons/agent-runtimes]].
- Actualizado [[index.md]] con el mapa completo de conocimiento listo para Obsidian.

## [2026-10-09] feature | Capa de Memoria Persistente y Configuraciones
- Creado el directorio `memory/` para desacoplar y persistir configuraciones del sistema, usuario, MCP y estado activo.
- Añadidos [[memory/system-config]], [[memory/user-preferences]], [[memory/mcp-registry]] y [[memory/active-state]].
- Creada herramienta CLI en Python [[tools/mem|tools/mem.py]] para inspección y mutación rápida de estados desde la terminal.
- Actualizado [[SCHEMA.md]] con el nuevo **Protocolo Memory** y actualizado [[index.md]].

