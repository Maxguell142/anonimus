"""
Terminal CLI for Anonymous (CLI Mode in Warp / PowerShell / Bash).
Uses Rich for modern styling, tables, trees, and colorized cyber outputs.
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Prompt
from rich.text import Text

from anonymous.core.dispatcher import dispatcher
from anonymous.core.os_adapter import os_adapter
from anonymous.engines.red.ptt import ptt_engine
from anonymous.core.session import session_manager

console = Console()


def print_banner():
    sys_info = os_adapter.get_system_info()
    banner_text = Text()
    banner_text.append("⚡ ANONYMOUS ⚡\n", style="bold cyan")
    banner_text.append("Hybrid Cybersecurity Assistant (Red + Blue + Ops)\n", style="bold green")
    banner_text.append(
        f"[{sys_info['os']} | IP: {sys_info['local_ip']} | AgentShield: ACTIVE | Python {sys_info['python_version']}]",
        style="dim white",
    )
    console.print(
        Panel(banner_text, border_style="cyan", subtitle="Escribe 'help' para comandos o escribe tu consulta")
    )


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
    print_banner()

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]anonymous[/bold green] [bold yellow]>[/bold yellow]").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "salir", "q"):
                console.print("[bold cyan]Cerrando sesión de Anonymous. ¡Hasta luego![/bold cyan]")
                break

            # Dispatch
            res = dispatcher.process_input(user_input)

            if res.get("type") == "confirmation_required":
                console.print(Panel(res["message"], title="🛡️ AgentShield Alerta", border_style="yellow"))
                confirm = Prompt.ask("[bold red]¿Confirmar ejecución?[/bold red] (s/n)", default="n").strip().lower()
                if confirm in ("s", "si", "y", "yes"):
                    res = dispatcher.process_input(user_input, confirmed_by_user=True)
                else:
                    console.print("[yellow]Operación cancelada por el usuario.[/yellow]")
                    continue

            # Render output based on result type
            t = res.get("type")
            if t == "scan":
                display_scan_results(res["data"])
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
