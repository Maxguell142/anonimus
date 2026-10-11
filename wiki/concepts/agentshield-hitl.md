---
type: concept
title: AgentShield & Human-In-The-Loop (HITL)
tags:
  - concept
  - security
  - guardrails
  - hitl
  - ecc
created: 2026-10-09
updated: 2026-10-09
---

# AgentShield & Human-In-The-Loop (HITL) - Contención y Seguridad de Agentes

> **Inspirado en:** [[ecc-agents]] y desplegado en [[anonymous]].

---

## 1. El Problema del Agente Autónomo sin Supervisión

Cuando un modelo de lenguaje (LLM) tiene la capacidad de emitir comandos en la terminal o realizar llamadas de red, existe el riesgo de:
* **Alucinación destructiva:** El modelo puede sugerir borrar archivos esenciales (`rm -rf /`, `del /f`).
* **Desbordamiento de alcance (*Out-of-Scope*):** Escanear o atacar accidentalmente IPs públicas o redes no autorizadas.
* **Fuga de credenciales o reverse shells:** Inyección de payloads de red sin el consentimiento explícito del operador.

---

## 2. El Mecanismo AgentShield

**AgentShield** actúa como un filtro determinista interpuesto entre el cerebro (LLM) y el sistema operativo:

```mermaid
flowchart LR
    LLM["Propuesta de Comando / Acción"] --> Filter{"AgentShield\nClasificador de Riesgo"}
    
    Filter -->|LOW (ej. ping local, info)| AutoExec["Ejecución Automática"]
    Filter -->|MEDIUM / HIGH (ej. scan externo, script)| Gate{"HITL Gate\n¿Usuario confirma? [S/n]"}
    Filter -->|CRITICAL (ej. borrar disco)| Block["Bloqueo Inmediato"]
    
    Gate -->|Sí| AutoExec
    Gate -->|No| Cancel["Operación Abortada"]
```

---

## 3. Matriz de Niveles de Riesgo

| Nivel | Tipo de Operaciones | Política de Ejecución |
| :--- | :--- | :--- |
| **`LOW`** | Consultas RAG, diagnósticos locales, `ping 127.0.0.1`, lectura de estado. | **Auto-aprobado:** Ejecución inmediata y transparente. |
| **`MEDIUM`** | Escaneo de puertos a hosts de red externa, lectura de directorios del sistema. | **Requiere HITL:** Se pausa y solicita confirmación interactiva. |
| **`HIGH`** | Modificación de reglas de red, llamadas a herramientas ofensivas activas. | **Requiere HITL:** Alerta explícita en amarillo/rojo con detalle del riesgo. |
| **`CRITICAL`** | Eliminación masiva del sistema de archivos, ejecución de comandos ofuscados. | **Bloqueo Total:** Rechazado por política de seguridad inmutable. |

---

## 4. Implementación en [[anonymous]]

En `anonymous/guardrails/agent_shield.py`, cualquier comando pasa por `evaluate_command()` o `evaluate_action()`. Si el usuario escribe `scan 192.168.1.50`, el despachador detecta que es un destino remoto y emite:
```text
⚠️ [AgentShield] Se requiere confirmación para escanear '192.168.1.50' (Nivel: MEDIUM).
¿Deseas autorizar la ejecución? (S/n):
```

---

## 5. Enlaces Relacionados
* [[ecc-agents]] - Origen de las directrices de contención y seguridad.
* [[anonymous]] - Plataforma donde protege la ejecución de comandos.
* [[ptt-task-tree]] - Las fases que son vigiladas por este escudo.
