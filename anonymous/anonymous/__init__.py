"""
Anonymous - Cybersecurity Hybrid Assistant
Fusion of PentestGPT, Cyber RAG, OpenJarvis, Jarvis, and ECC Guardrails.
"""

__version__ = "0.1.0"
__author__ = "Anonymous Project"

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

