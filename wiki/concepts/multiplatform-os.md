---
type: concept
title: Ejecución Multiplataforma Nativa (Sin Docker)
tags:
  - concept
  - cross-platform
  - os-adapter
  - hardware-optimization
created: 2026-10-09
updated: 2026-10-09
---

# Ejecución Multiplataforma Nativa (Windows & Linux sin Docker)

> **Implementado en:** [[anonymous]] para garantizar soporte en Windows 11 y Linux sin penalización de rendimiento.

---

## 1. El Dilema de Docker en Equipos de 8 GB de RAM

Muchos proyectos de ciberseguridad y LLMs recomiendan empaquetar todo dentro de contenedores Docker. Sin embargo, en un equipo con **8 GB de RAM** (como un AMD Ryzen 5 5500U en Windows 11):
* Docker Desktop en Windows requiere el subsistema **WSL2 (`vmmem`)**.
* `vmmem` reserva de inmediato entre **2.0 GB y 3.5 GB de memoria RAM**.
* Al sumar el consumo base de Windows 11 (3.5 GB - 4.5 GB), el sistema entra en paginación en disco (*swapping*), provocando congelamientos y pérdida masiva de fluidez.

---

## 2. La Solución: Capa de Abstracción `OSAdapter`

En lugar de aislar el sistema mediante una máquina virtual pesada, [[anonymous]] implementa un adaptador de sistema operativo ligero (`anonymous/core/os_adapter.py`) que traduce las llamadas de forma agnóstica:

```mermaid
flowchart TD
    CoreLogic["Lógica de Anonymous (Python Puro)"] --> OSAdapter{"anonymous/core/os_adapter.py\nsys.platform"}

    OSAdapter -->|win32 (Windows 11)| WinCommands["Comandos Windows:\n• ping -n 4\n• Sockets nativos\n• PowerShell / CMD"]
    OSAdapter -->|linux (Kali / Ubuntu)| LinuxCommands["Comandos Linux:\n• ping -c 4\n• Sockets nativos\n• Bash / Zsh"]
```

---

## 3. Reglas de Ingeniería para Compatibilidad Universal

1. **Gestión de Rutas con `pathlib.Path`:**  
   Nunca usar cadenas fijas con barras invertidas (`C:\...`). `pathlib` normaliza automáticamente los separadores en `\` (Windows) o `/` (Linux).
2. **Uso de Sockets de Red en Python Puro:**  
   En lugar de obligar al usuario a tener `nmap` instalado, el módulo `recon.py` utiliza la biblioteca estándar `socket` con `ThreadPoolExecutor`. Funciona exactamente igual en Windows y Linux sin compilar binarios externos.
3. **Manejo de Codificación UTF-8:**  
   Windows suele utilizar `cp1252` por defecto en la terminal. El sistema reconfigura explícitamente `sys.stdout` y `sys.stderr` a `utf-8` para evitar errores al renderizar símbolos o emojis.

---

## 4. Enlaces Relacionados
* [[anonymous]] - Proyecto donde opera el `OSAdapter`.
* [[openjarvis]] - Framework con componentes multiplataforma.
* [[architecture-matrix]] - Comparativa de consumos y dependencias.
