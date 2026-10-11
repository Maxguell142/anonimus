---
type: memory-config
category: preferences
title: Preferencias y Directrices del Usuario
created: 2026-10-09
updated: 2026-10-09
tags:
  - memory
  - preferences
  - developer-profile
---

# Preferencias y Directrices del Usuario (`user-preferences.md`)

Este archivo define la memoria de **hábitos de trabajo, estilo y preferencias** del operador para que el agente mantenga consistencia a lo largo de todas las sesiones.

---

## 1. Perfil y Comunicación

```yaml
profile:
  user_name: "Max"
  primary_language: "es"         # Español
  tone: "técnico, conciso, directo, amigable"
  explanation_level: "práctico"  # Explicaciones claras sin tecnicismos innecesarios
  formatting: "GitHub-flavored Markdown con enlaces clicables y diagramas Mermaid"
```

---

## 2. Reglas de Programación y Desarrollo

```yaml
development_rules:
  no_docker_rule: true           # Nunca sugerir Docker a menos que el usuario lo pida explícitamente
  lightweight_first: true        # Priorizar soluciones en Python estándar sin dependencias pesadas
  test_before_finish: true       # Probar scripts y comandos localmente antes de darlos por concluidos
  preserve_codebases: true       # Mantener intactos los repositorios originales (anonimus/*-main)
  single_source_of_truth: "wiki" # Toda decisión arquitectónica importante se documenta en la wiki
```

---

## 3. Preferencias de Interfaz y Herramientas

```yaml
tools_preferences:
  cli_terminal: "Warp"
  gui_preferred_theme: "Cyberpunk / Dark Slate (#0a0e14)"
  voice_input: "Web Speech API nativa en navegador"
  knowledge_tool: "Obsidian"     # Almacén de notas y wiki
```

---

## 4. Política de Seguridad (AgentShield)

```yaml
security_preferences:
  hitl_gate_enabled: true        # Solicitar confirmación [S/n] para acciones MEDIUM o HIGH
  remote_ip_scan_alert: true     # Nunca escanear una IP que no sea localhost sin preguntar
  read_only_default_mode: false  # Se permite ejecución de scripts creados en el workspace
```
