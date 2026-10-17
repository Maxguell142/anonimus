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

## [2026-10-16] feature | Boceto Web Táctico y Documentación Integral en Obsidian
- Creado el módulo web independiente en `pagina/` con `index.html`, `styles.css`, `app.js` y `server.py`.
- Implementado servidor nativo en Python enlazado a `0.0.0.0:8080`, permitiendo transmisión local (`http://localhost:8080`) y acceso por red Wi-Fi (`http://10.0.5.49:8080`).
- Diseñado boceto de interfaz HUD táctico (inspirado en Stark Industries / Cyberpunk) con radar en HTML5 Canvas, escáner de sockets TCP, árbol de tareas PTT interactivo, asesor RAG normativo (OWASP/MITRE/CIS) y arnés de seguridad AgentShield (HITL).
- Redactada la documentación completa para Obsidian en [[projects/documentacion-proyecto-anonimus]] abordando contexto, resolución de problemas en el mundo real y flujo de interacción.
- Replicada la documentación en `C:\Users\maxgu\Documents\Obsidian Vault\documentacion-proyecto-anonimus.md` para visibilidad inmediata en ambos vaults.

## [2026-10-17] ingest | Kali MCP → Anonymous + wiki
- Copiados 45 archivos `.md` de `kali-mcp-main` a `wiki/kali-mcp/` y `anonymous/knowledge/kali/`.
- Creada página [[projects/kali-mcp]] y catálogo [[commands]].
- Anonymous: motor `engines/ops/kali_mcp.py` (Docker compose HITL, salud MCP, sesiones pasivas, búsqueda de playbooks). `kali-audit` y `kali exec` ofensivo se rechazan.
- Actualizados [[index]], [[memory/system-config]] (Docker opcional), [[memory/mcp-registry]], [[projects/anonymous]] y `anonymous/.mcp.json`.


