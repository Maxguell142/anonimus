#!/usr/bin/env python3
"""
Launcher for Anonymous (Cybersecurity Hybrid Assistant).

Usage:
    python run.py          # Lanza la interfaz interactiva en Terminal (CLI)
    python run.py --gui    # Lanza el panel de control web en el navegador (GUI)
"""

import sys
import argparse
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main():
    parser = argparse.ArgumentParser(
        description="Anonymous - Plataforma Híbrida de Ciberseguridad"
    )
    parser.add_argument(
        "--gui", "-g",
        action="store_true",
        help="Iniciar en modo interfaz gráfica web (dashboard en navegador)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=7860,
        help="Puerto para la interfaz web (por defecto: 7860)",
    )

    args = parser.parse_args()

    if args.gui:
        from anonymous.server import run_server
        run_server(port=args.port, open_browser=True)
    else:
        from anonymous.cli import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()
