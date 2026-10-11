---
type: concept
title: Pentesting Task Tree (PTT)
tags:
  - concept
  - methodology
  - red-team
  - ptt
created: 2026-10-09
updated: 2026-10-09
---

# Pentesting Task Tree (PTT) - Metodología de Árbol de Tareas

> **Implementado en:** [[pentestgpt]] y adaptado en [[anonymous]].

---

## 1. ¿Qué es el Pentesting Task Tree?

El **Pentesting Task Tree (PTT)** es una estructura jerárquica de datos y toma de decisiones que modela el razonamiento de un auditor de seguridad durante una prueba de penetración.

A diferencia de una lista plana de tareas pendientes (*To-Do list*), el PTT:
1. **Es dependiente del contexto:** Una fase solo se desbloquea o refina cuando las subtareas de la fase anterior han producido resultados (ej: no se buscan vulnerabilidades en un puerto que no está verificado como abierto).
2. **Gestiona estados dinámicos:** Cada nodo puede estar en estado `pending`, `in_progress`, `completed` o `failed`.
3. **Mantiene el foco del LLM:** Evita que el agente se desvíe o intente fases avanzadas (como exploits) sin haber completado el reconocimiento básico.

---

## 2. Diagrama de Fases del PTT

```mermaid
flowchart TD
    subgraph Phase1["1. Reconnaissance"]
        T1["recon-01: Identificación y resolución DNS"]
        T2["recon-02: Detección de host vivo (Ping)"]
    end

    subgraph Phase2["2. Scanning & Enumeration"]
        T3["scan-01: Escaneo de puertos TCP"]
        T4["scan-02: Banner grabbing de servicios"]
    end

    subgraph Phase3["3. Vulnerability Analysis"]
        T5["vuln-01: Cruce de servicios con CVE/RAG"]
        T6["vuln-02: Evaluación de credenciales por defecto"]
    end

    subgraph Phase4["4. Reporting & Remediation"]
        T7["rep-01: Generación de reporte y mitigación"]
    end

    T1 --> T2 --> T3 --> T4 --> T5 --> T6 --> T7
```

---

## 3. Implementación en [[anonymous]]

En `anonymous/engines/red/ptt.py`, el árbol está respaldado por SQLite:
* Cuando el usuario ejecuta un escaneo de puertos (`scan 127.0.0.1`), el motor actualiza de forma autónoma el estado de `scan-01` a `completed`, registrando cuántos puertos abiertos se encontraron.
* Esto permite que tanto la interfaz CLI en terminal como el Dashboard Web reflejen visualmente el avance del pentest en tiempo real.

---

## 4. Enlaces Relacionados
* [[pentestgpt]] - Proyecto donde se originó el PTT.
* [[anonymous]] - Implementación nativa y reactiva del árbol.
* [[agentshield-hitl]] - Barrera de control antes de avanzar a fases de alto riesgo.
