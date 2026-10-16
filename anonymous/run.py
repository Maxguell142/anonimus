#!/usr/bin/env python3
"""
Launcher for Anonymous (Cybersecurity Hybrid Assistant).

Usage:
    python run.py          # Lanza la interfaz interactiva en Terminal (CLI)
    python run.py --gui    # Lanza la interfaz gráfica de escritorio
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
        "--gui", "--desktop", "-g",
        dest="desktop",
        action="store_true",
        help="Iniciar la interfaz gráfica de escritorio (Tkinter)",
    )

    args = parser.parse_args()

    if args.desktop:
        from anonymous.desktop import run_desktop
        run_desktop()
    else:
        from anonymous.cli import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()
