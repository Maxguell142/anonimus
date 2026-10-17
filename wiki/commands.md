---
type: catalog
title: Catálogo de comandos Anonymous + Kali MCP
created: 2026-10-17
updated: 2026-10-17
tags:
  - commands
  - cli
  - desktop
  - kali
---

# Catálogo de comandos

Dos modos de uso, **mismo despachador**:

| Modo | Cómo entrar | Superficie |
| :--- | :--- | :--- |
| Terminal | `python run.py` | CLI Rich (Warp / PowerShell) |
| Escritorio | `python run.py --gui` | Ventana Tkinter (no es página web) |

Los comandos de abajo funcionan en ambos. También hay frases en español equivalentes.

---

## 1. Núcleo Anonymous (siempre disponible, sin Docker)

| Comando | Qué hace | Ejemplo natural |
| :--- | :--- | :--- |
| `help` / `ayuda` / `comandos` | Lista esta ayuda | `comandos` |
| `status` / `briefing` / `estado` | SO, IP, PTT, hallazgos, estado Kali MCP | `estado del sistema` |
| `scan <ip> [puertos]` | Escaneo TCP nativo Python | `escaneá localhost` |
| `ping <host>` | ICMP vía OSAdapter | `está vivo 127.0.0.1` |
| `rag <consulta>` | Base normativa local (OWASP / MITRE / CIS) | `qué dice OWASP sobre inyección SQL` |
| `ptt` | Árbol de tareas | `mostrá el árbol de tareas` |
| `ptt reset` | Reinicia el PTT | — |
| `findings` / `hallazgos` | Hallazgos de sesión SQLite | `mostrá los hallazgos` |
| `report` / `reporte` | Resumen defensivo | `armá un informe` |
| `exit` / `quit` / `salir` | Cierra solo el CLI | — |

HITL: `scan` y `ping` a IPs no locales piden confirmación (CLI: S/n; escritorio: diálogo).

---

## 2. Kali MCP (opcional, Docker)

Requisito: Docker Desktop + checkout `kali-mcp-main`. Endpoint MCP: `http://127.0.0.1:666/mcp`.

| Comando | Qué hace |
| :--- | :--- |
| `kali status` / `kali health` | Docker, compose.yml, salud MCP, sesión activa |
| `kali start` / `kali up` | `docker compose up -d` (HITL; gasta RAM) |
| `kali stop` / `kali down` | `docker compose down` (HITL) |
| `kali-start <objetivo>` | Carpeta de sesión **pasiva** en `~/.anonymous/kali_sessions/` |
| `kali knowledge <tema>` | Busca en la copia local de playbooks markdown |
| `kali-finish` | Cierra la sesión activa |
| `kali-audit` | **No se ejecuta.** Mensaje de límite (sin explotación automática) |
| `kali exec …` | **Bloqueado.** No hay shell libre hacia el contenedor |

Frases: `levantá kali`, `estado de kali`, `parar kali`, `playbook ssh`, `cerrar sesión kali`.

Alcance de sesión Anonymous: solo **passive**. Alcances credential/full del repo original no se inicializan aquí.

---

## 3. Slash commands del repo fuente (kali-mcp-main)

Viven en `.claude/commands/`, `.gemini/commands/` y `.opencode/commands/`. Anonymous no los reimplementa como auditoría ofensiva.

| Slash | En kali-mcp-main | En Anonymous |
| :--- | :--- | :--- |
| `/kali-start` | Sesión + pregunta de alcance | `kali-start` pasivo |
| `/kali-audit` | nmap + sub-agentes (puede ser full) | Rechazado |
| `/kali-finish` | Reporte + consolidar knowledge | `kali-finish` cierra carpeta |

Copia literal de esos markdown: `wiki/kali-mcp/.claude/commands/`, etc.

---

## 4. Lanzadores

```bash
cd C:\Users\maxgu\Documents\anonimus\anonymous
python -m pip install -r requirements.txt
python run.py              # terminal
python run.py --gui        # escritorio Tkinter
python -m unittest discover -s tests -v
```

Variables opcionales (`.env`): `GEMINI_API_KEY`, `KALI_MCP_ROOT`, `KALI_MCP_URL`, `ANONYMOUS_SAFE_MODE`.

Ver [[projects/kali-mcp]] y [[projects/anonymous]].
