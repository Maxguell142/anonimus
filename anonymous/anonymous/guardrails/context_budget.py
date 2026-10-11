"""
Context Budget & Compression Manager (Inspired by ECC context-budget skill).
Prevents context window bloat, optimizes token efficiency, and compresses conversation history.
"""

from typing import List, Dict, Any


class ContextBudgetManager:
    """Monitors and compresses context payload sent to LLM."""

    def __init__(self, max_history_turns: int = 10, max_token_estimate: int = 8000):
        self.max_history_turns = max_history_turns
        self.max_token_estimate = max_token_estimate

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (approx 4 chars per token)."""
        return max(1, len(text) // 4)

    def prune_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Keeps the most relevant recent turns, summarizing older ones if needed."""
        if len(history) <= self.max_history_turns:
            return history

        # Keep system/initial context and the most recent N turns
        pruned = history[-self.max_history_turns:]
        return pruned

    def compress_tool_output(self, output: str, max_lines: int = 40) -> str:
        """Compresses voluminous tool/terminal outputs to avoid wasting tokens."""
        lines = output.splitlines()
        if len(lines) <= max_lines:
            return output

        half = max_lines // 2
        compressed = (
            lines[:half]
            + [f"\n... [Salida recortada por ContextBudget: {len(lines) - max_lines} líneas omitidas] ...\n"]
            + lines[-half:]
        )
        return "\n".join(compressed)


context_budget = ContextBudgetManager()
