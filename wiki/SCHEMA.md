---
type: schema
created: 2026-10-09
updated: 2026-10-09
tags:
  - meta
  - schema
  - architecture
---

# Wiki Schema & Governance Guidelines

Este documento define la estructura, reglas y flujos de trabajo para el mantenimiento de la **LLM Wiki del Ecosistema de Ciberseguridad y Asistentes** (`anonimus`).

---

## 1. Principios de Diseño de la Wiki

1. **Persistencia y Compilación Incremental:**  
   La wiki no es un simple volcado de texto. Es un artefacto persistente que compila y sintetiza el conocimiento entre las fuentes en bruto (`PentestGPT`, `OpenJarvis`, `cybersecurity-rag`, `jarvis`, `ECC`, `Anonymous`) y las consultas del usuario.
2. **Compatibilidad Nativa con Obsidian:**  
   * Enlaces bidireccionales mediante sintaxis `[[nombre-de-pagina]]`.
   * Encabezados YAML frontmatter en cada archivo (`type`, `tags`, `updated`, etc.).
   * Uso de diagramas Mermaid estándar para visualización gráfica en el panel de grafos (*Graph View*).
3. **El LLM como Bibliotecario / Mantenedor:**  
   El LLM escribe, enlaza, detecta contradicciones y actualiza los resúmenes; el usuario guía la exploración y toma las decisiones estratégicas.

---

## 2. Taxonomía de Directorios

```text
wiki/
├── index.md                 # Catálogo general organizado por secciones
├── log.md                   # Registro cronológico inmutable de operaciones
├── SCHEMA.md                # Este documento de reglas y convenciones
├── memory/                  # Memoria persistente de configuraciones y estado activo
│   ├── system-config.md     # Hardware, puertos, modelos y límites
│   ├── user-preferences.md  # Preferencias, idioma, terminal y directrices
│   ├── mcp-registry.md      # Plantillas y servidores MCP listos para conectar
│   └── active-state.md      # Estado dinámico de trabajo (objetivo activo, PTT)
├── tools/                   # Herramientas CLI auxiliares de la Wiki
│   └── mem.py               # CLI para consultar, cambiar estados y sincronizar MCP
├── projects/                # Páginas de análisis profundo por repositorio
│   ├── pentestgpt.md
│   ├── cybersecurity-rag.md
│   ├── openjarvis.md
│   ├── jarvis.md
│   ├── ecc-agents.md
│   └── anonymous.md
├── concepts/                # Conceptos transversales y patrones de ingeniería
│   ├── ptt-task-tree.md
│   ├── agentshield-hitl.md
│   ├── multiplatform-os.md
│   └── rag-vs-wiki.md
└── comparisons/             # Matrices comparativas, tradeoffs y síntesis
    ├── architecture-matrix.md
    └── agent-runtimes.md
```

---

## 3. Protocolos de Operación

### Protocolo `Ingest` (Ingesta de Nuevas Fuentes o Cambios)
1. Leer y analizar la fuente en bruto o el nuevo código.
2. Crear o actualizar la página correspondiente en `projects/` o `concepts/`.
3. Mantener y actualizar referencias cruzadas `[[...]]`.
4. Señalar sinergias, incompatibilidades o contradicciones con otros proyectos.
5. Actualizar `index.md` con el enlace y un resumen de una línea.
6. Añadir entrada fechada en `log.md` con formato estricto:  
   `## [YYYY-MM-DD] ingest | <Título o Acción>`

### Protocolo `Query` (Consulta y Síntesis)
1. El LLM consulta `index.md` primero para ubicar las páginas relevantes.
2. Si una consulta genera un análisis profundo, una comparación nueva o un descubrimiento clave, **se archiva como una nueva página** en `concepts/` o `comparisons/`.

### Protocolo `Lint` (Salud y Consistencia)
1. Detectar páginas huérfanas (sin enlaces entrantes).
2. Verificar enlaces rotos o inexistentes.
3. Actualizar fechas en el frontmatter YAML.

### Protocolo `Memory` (Gestión de Configuración y Estado)
1. **Consulta Previa Obligatoria:** Antes de ejecutar acciones complejas o sugerir tecnologías, el LLM debe leer `memory/system-config.md` y `memory/user-preferences.md` para respetar el límite de RAM, la regla *No Docker* y las preferencias del usuario.
2. **Persistencia de Cambios:** Si el usuario modifica una configuración (ej. un puerto, una API key o un nuevo servidor MCP), el LLM debe actualizar de inmediato el archivo correspondiente en `memory/` y documentar el cambio en la tabla de historial de la página.
3. **Sincronización de Estado Dinámico:** Al concluir auditorías o tareas de penetración, el LLM actualiza `memory/active-state.md` con el objetivo actual, puertos abiertos detectados y fase PTT.

