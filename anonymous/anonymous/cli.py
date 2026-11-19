"""
Terminal CLI for Anonymous (CLI Mode in Warp / PowerShell / Bash).
Uses Rich for modern styling, tables, trees, and colorized cyber outputs.
"""

import sys
from getpass import getpass
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.prompt import IntPrompt, Prompt
from rich.text import Text

from anonymous.core.dispatcher import dispatcher
from anonymous.core.os_adapter import os_adapter
from anonymous.engines.red.ptt import ptt_engine
from anonymous.core.session import session_manager
from anonymous.settings import BACKENDS, PROVIDERS, SettingsError, apply_runtime_settings, settings_store

console = Console()


def print_banner(profile_name: str = ""):
    sys_info = os_adapter.get_system_info()
    banner_text = Text()
    banner_text.append("⚡ ANONYMOUS ⚡\n", style="bold cyan")
    banner_text.append("Hybrid Cybersecurity Assistant (Red + Blue + Ops)\n", style="bold green")
    banner_text.append(
        f"[{sys_info['os']} | IP: {sys_info['local_ip']} | AgentShield: ACTIVE | Python {sys_info['python_version']}]",
        style="dim white",
    )
    if profile_name:
        banner_text.append(f"\nPerfil local: {profile_name}", style="dim white")
    console.print(
        Panel(
            banner_text,
            border_style="cyan",
            subtitle="Escribe 'help' para comandos, 'config' para ajustes o tu consulta",
        )
    )


def _show_settings() -> None:
    settings = settings_store.load()
    table = Table(title="Configuración de Anonymous", border_style="cyan")
    table.add_column("Área", style="cyan")
    table.add_column("Valor")
    table.add_row("Proveedor IA", settings["ai_provider"])
    table.add_row("Modelo Ollama", settings["ollama_model"])
    table.add_row("Modelo Gemini", settings["gemini_model"])
    table.add_row("Clave Gemini", "configurada" if settings_store.get_api_key() else "no configurada")
    table.add_row("Entorno Kali", settings["kali_backend"])
    if settings["kali_backend"] == "cloud":
        ssh = settings["cloud_ssh"]
        connection = f"{ssh['username']}@{ssh['host']}:{ssh['port']}" if ssh["host"] else "sin configurar"
        table.add_row("Kali cloud por SSH", connection)
    else:
        table.add_row(
            "MCP seleccionado",
            settings["mcp_urls"].get(settings["kali_backend"], "no aplica") or "sin endpoint",
        )
    table.add_row("Nombre visible", settings["user_name"] or "sin configurar")
    console.print(table)


def _configure_settings() -> None:
    settings = settings_store.load()
    console.print(
        "[dim]Entornos: native = herramientas locales integradas; docker = MCP Docker existente; "
        "cloud = Kali por SSH con clave y host key verificada; virtualbox = MCP externo. "
        "El descubrimiento sigue limitado y requiere confirmación.[/dim]"
    )
    settings["ai_provider"] = Prompt.ask(
        "Proveedor de IA", choices=list(PROVIDERS), default=settings["ai_provider"]
    )
    settings["ollama_base_url"] = Prompt.ask(
        "URL base de Ollama", default=settings["ollama_base_url"]
    )
    settings["ollama_model"] = Prompt.ask("Modelo Ollama", default=settings["ollama_model"])
    settings["gemini_model"] = Prompt.ask("Modelo Gemini", default=settings["gemini_model"])
    settings["gemini_fallback_model"] = Prompt.ask(
        "Modelo Gemini de respaldo", default=settings["gemini_fallback_model"]
    )
    settings["ollama_timeout"] = IntPrompt.ask(
        "Timeout Ollama (segundos)", default=settings["ollama_timeout"]
    )
    settings["gemini_timeout"] = IntPrompt.ask(
        "Timeout Gemini (segundos)", default=settings["gemini_timeout"]
    )
    settings["kali_backend"] = Prompt.ask(
        "Entorno Kali",
        choices=list(BACKENDS),
        default=settings["kali_backend"],
    )
    for backend in ("docker", "virtualbox"):
        settings["mcp_urls"][backend] = Prompt.ask(
            f"URL MCP de {backend}",
            default=settings["mcp_urls"][backend],
        )
    ssh = settings["cloud_ssh"]
    ssh["host"] = Prompt.ask("Host o IPv4 de Kali cloud", default=ssh["host"])
    ssh["username"] = Prompt.ask("Usuario SSH de Kali", default=ssh["username"])
    ssh["port"] = IntPrompt.ask("Puerto SSH", default=ssh["port"])
    ssh["key_path"] = Prompt.ask("Ruta de la clave privada SSH", default=ssh["key_path"])
    ssh["known_hosts"] = Prompt.ask(
        "Ruta de known_hosts con la host key aceptada",
        default=ssh["known_hosts"],
    )
    settings["user_name"] = Prompt.ask(
        "Nombre visible del perfil local", default=settings["user_name"]
    )
    api_key = ""
    clear_api_key = False
    if settings["ai_provider"] == "google":
        api_key = getpass("Clave API Gemini (Enter conserva la guardada): ").strip()
        if not api_key:
            clear_api_key = (
                Prompt.ask(
                    "¿Eliminar la clave del almacén del sistema? (GEMINI_API_KEY no se borra) (s/n)",
                    choices=["s", "n"],
                    default="n",
                )
                == "s"
            )

    settings_store.save(settings)
    if api_key or clear_api_key:
        try:
            settings_store.set_api_key(api_key if api_key else "")
        except SettingsError:
            apply_runtime_settings(settings)
            raise
    apply_runtime_settings(settings)
    console.print("[bold green]Ajustes guardados y aplicados.[/bold green]")


def display_scan_results(data: dict):
    ports = data.get("ports", [])
    if not ports:
        console.print(f"[yellow]No se detectaron puertos abiertos en {data.get('target')}.[/yellow]")
        return

    table = Table(title=f"Resultados de Escaneo en {data.get('target')}", border_style="green")
    table.add_column("Puerto", style="cyan", justify="right")
    table.add_column("Estado", style="green")
    table.add_column("Servicio", style="magenta")
    table.add_column("Detalle / Banner", style="dim")

    for p in ports:
        table.add_row(str(p["port"]), "OPEN", p["service"], p.get("banner", "") or "-")

    console.print(table)


def display_ptt_tree(tasks: list):
    tree = Tree("[bold cyan]🌳 Pentesting Task Tree (PTT)[/bold cyan]")
    phases = {}
    for t in tasks:
        ph = t.get("phase", "General")
        if ph not in phases:
            phases[ph] = []
        phases[ph].append(t)

    for ph, t_list in phases.items():
        branch = tree.add(f"[bold yellow]{ph}[/bold yellow]")
        for t in t_list:
            status = t.get("status", "pending")
            if status == "completed":
                badge = "[bold green]✔ COMPLETADO[/bold green]"
            elif status == "in_progress":
                badge = "[bold cyan]⏳ EN CURSO[/bold cyan]"
            elif status == "failed":
                badge = "[bold red]✖ FALLIDO[/bold red]"
            else:
                badge = "[dim]○ PENDIENTE[/dim]"

            detail = f" [dim]({t.get('details')})[/dim]" if t.get("details") else ""
            branch.add(f"{badge} {t['name']}{detail}")

    console.print(tree)


def display_findings(findings: list):
    if not findings:
        console.print("[dim]No hay hallazgos registrados aún.[/dim]")
        return

    table = Table(title="🛡️ Hallazgos y Vulnerabilidades Detectadas", border_style="red")
    table.add_column("Objetivo", style="cyan")
    table.add_column("Severidad", style="bold red")
    table.add_column("Título", style="white")
    table.add_column("Detalle", style="dim")

    for f in findings:
        table.add_row(f["target"], f["severity"], f["title"], f.get("details", "") or "-")

    console.print(table)


def main():
    settings = None
    try:
        settings = apply_runtime_settings()
    except (SettingsError, ValueError, RuntimeError, OSError) as exc:
        console.print(f"[bold red]No se pudieron aplicar los ajustes guardados:[/bold red] {exc}")
    print_banner(settings["user_name"] if settings else "")

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]anonymous[/bold green] [bold yellow]>[/bold yellow]").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "salir", "q"):
                console.print("[bold cyan]Cerrando sesión de Anonymous. ¡Hasta luego![/bold cyan]")
                break
            if user_input.lower() in ("config", "configuracion", "configuración"):
                _configure_settings()
                continue
            if user_input.lower() in ("config show", "config mostrar"):
                _show_settings()
                continue

            # Dispatch
            res = dispatcher.process_input(user_input)

            if res.get("type") == "confirmation_required":
                console.print(Panel(res["message"], title="🛡️ AgentShield Alerta", border_style="yellow"))
                confirm = Prompt.ask("[bold red]¿Confirmar ejecución?[/bold red] (s/n)", default="n").strip().lower()
                if confirm in ("s", "si", "y", "yes"):
                    res = dispatcher.confirm_pending_action(res)
                else:
                    console.print("[yellow]Operación cancelada por el usuario.[/yellow]")
                    continue

            # Render output based on result type
            t = res.get("type")
            if t == "scan":
                display_scan_results(res["data"])
                if res.get("advice"):
                    console.print(Panel(res["advice"], title="🛡️ Asesoría Blue Team", border_style="green"))
            elif t == "ptt":
                display_ptt_tree(res["tasks"])
            elif t == "findings":
                display_findings(res["findings"])
            elif t in ("help", "status", "rag"):
                console.print(Panel(res.get("message", ""), title=f"⚡ {t.upper()}", border_style="cyan"))
            elif t == "ping":
                color = "green" if res.get("alive") else "red"
                console.print(f"[{color}]{res.get('message')}[/{color}]")
            else:
                console.print(f"\n{res.get('message', '')}")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Sesión interrumpida. Cerrando...[/dim]")
            break
        except Exception as e:
            console.print(f"[bold red]Error en comando:[/bold red] {str(e)}")


if __name__ == "__main__":
    main()
