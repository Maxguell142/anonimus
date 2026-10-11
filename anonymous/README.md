# ⚡ Anonymous - Hybrid Cybersecurity Platform

Asistente híbrido unificado de ciberseguridad que fusiona:
- **PentestGPT**: Lógica de auditoría ofensiva y Árbol de Tareas de Pentesting (PTT).
- **Cybersecurity RAG Assistant**: Asesor defensivo sobre normativas OWASP Top 10, MITRE ATT&CK y CIS Controls.
- **OpenJarvis / Jarvis**: Orquestador central de tareas, resumen operativo diario e interacción por voz.
- **ECC AgentShield**: Arnés de validación de comandos y Human-In-The-Loop para máxima seguridad.

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

### 2. Modo Panel Gráfico Web (GUI):
```bash
python run.py --gui
```
Abre automáticamente tu navegador en `http://127.0.0.1:7860` con chat, monitoreo visual de PTT, escáner rápido y asesor RAG.

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
| `ping <host>` | Verificación de conectividad agnóstica de sistema operativo. |
| `help` | Ayuda y listado de comandos. |

---

## ⚙️ Configuración Opcional de Inteligencia en la Nube
Copia `.env.example` a `.env` y agrega tu `GEMINI_API_KEY` para activar el razonamiento con Google Gemini Flash. El modelo predeterminado es `gemini-3.8-flash`; puedes cambiarlo con `GEMINI_MODEL`.  
*Nota: Si no agregas la API key, Anonymous funcionará de todos modos con sus motores locales integrados.*
