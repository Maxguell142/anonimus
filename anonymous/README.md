# ⚡ Anonymous - Hybrid Cybersecurity Platform

Asistente híbrido unificado de ciberseguridad que fusiona:
- **PentestGPT**: Lógica de auditoría ofensiva y Árbol de Tareas de Pentesting (PTT).
- **Asesor defensivo local**: búsqueda en referencias OWASP Top 10, MITRE ATT&CK, CIS Controls v8 y NIST CSF 2.0.
- **Centro de control Anonymous**: monitoreo local del equipo, registro de eventos y comandos desde una interfaz de escritorio.
- **ECC AgentShield**: Arnés de validación de comandos y Human-In-The-Loop para máxima seguridad.
- **Kali MCP (opcional)**: Docker con Kali y MCP en `http://127.0.0.1:666/mcp`. Documentación copiada a la wiki. No ejecuta explotación automática.

---

## 🚀 Cómo ejecutar la Demo

### 0. Instalar dependencias
Desde la carpeta `anonymous`, instala las dependencias en el entorno virtual que vayas a usar:
```bash
python -m pip install -r requirements.txt
```

### 1. Modo Terminal interactivo (CLI en Warp / PowerShell / Bash):
```bash
python run.py
```

### 2. Modo gráfico de escritorio (HUD nativo):
```bash
python run.py --gui
```
Abre un centro de control de escritorio con métricas reales de CPU, memoria, disco y tráfico de red, un flujo Matrix, gráficos animados tipo pipes, registro de eventos, hallazgos y comandos. No muestra el reactor, objetivos ficticios ni contramedidas decorativas.

Los paneles se pueden arrastrar desde su encabezado, cambiar de tamaño desde la esquina inferior derecha y ocultar o volver a mostrar desde `PANELES`. La posición, el tamaño y la visibilidad se guardan en `~/.anonymous/desktop_layout.json`; `RESTABLECER DISTRIBUCIÓN` recupera la disposición inicial. Los botones `NORMAL`, `ATAQUE`, `DEFENSA`, `ÉXITO` y `ERROR` cambian los colores y el estado de la interfaz.

La ventana se implementa con Tkinter y `psutil`; no abre el navegador ni necesita un servidor web.

---

## 🛠️ Comandos Principales en la Terminal

| Comando | Descripción |
| :--- | :--- |
| `status` / `briefing` | Estado del sistema, IP local y resumen de tareas activas. |
| `scan <ip>` | Escáner multihilo de puertos TCP en Python nativo sin depender de nmap ni Docker. |
| `rag <consulta>` | Consulta instantánea a la base de conocimiento defensiva (OWASP, MITRE, CIS). |
| `ptt` | Muestra el árbol de tareas de penetración (Pentest Task Tree). |
| `ptt reset` | Reinicia el árbol de tareas de pentesting. |
| `findings` | Lista de vulnerabilidades y puertos abiertos detectados en la sesión. |
| `report` | Resumen defensivo de hallazgos y avance del PTT. |
| `ping <host>` | Verificación de conectividad agnóstica de sistema operativo. |
| `help` / `comandos` | Ayuda y listado de comandos. |
| `kali status` | Docker + salud del MCP Kali (`:666`). |
| `kali start` / `kali stop` | Levanta o para el contenedor (pide confirmación). |
| `kali-start <objetivo>` | Sesión pasiva de evidencias. |
| `kali knowledge <tema>` | Playbooks markdown copiados de kali-mcp. |
| `kali-finish` | Cierra la sesión Kali. |

`kali-audit` y `kali exec` ofensivo **no están habilitados** (límite de seguridad). Catálogo: `../wiki/commands.md`.

También se aceptan frases naturales como `mostrame el estado`, `revisá los puertos de localhost`, `comprobá conectividad con 127.0.0.1`, `ver tareas pendientes`, `armá un informe` y preguntas defensivas como `cómo proteger una API contra fuerza bruta`.

La base normativa funciona sin conexión y es una referencia práctica, no un catálogo exhaustivo ni una fuente legal actualizada automáticamente. Para uso operativo, valida las recomendaciones con la versión vigente de cada marco.

---

## ⚙️ Configuración Opcional de Inteligencia en la Nube
Copia `.env.example` a `.env` y agrega tu `GEMINI_API_KEY` para activar el razonamiento con Google Gemini Flash. El modelo predeterminado es `gemini-3.8-flash`; si falla o se agota el tiempo, se intenta `gemini-3.6-flash` y luego el modo local.  
El contexto de conversación se conserva durante la ejecución actual y no mezcla mensajes de ejecuciones anteriores.  
También entendés frases en español. Los escaneos y pings a objetivos no locales piden confirmación HITL tanto en la terminal como en la GUI de escritorio.  
*Nota: Si no agregas la API key, Anonymous funcionará de todos modos con sus motores locales integrados.*
