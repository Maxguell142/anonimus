"""
RAG Engine for Cybersecurity Regulations & Mitigation (Blue Team).
Retrieves relevant security framework controls and hardening recommendations.
"""

from typing import List, Dict, Any
import unicodedata
from anonymous.engines.blue.knowledge_base import KNOWLEDGE_ENTRIES


class RAGEngine:
    """Lightweight retrieval engine over cybersecurity frameworks."""

    def __init__(self, entries: List[Dict[str, Any]] = KNOWLEDGE_ENTRIES):
        self.entries = entries

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Finds top-k matching security guidelines based on query terms."""
        query_terms = set(self._normalize(query).replace(",", " ").replace(".", " ").split())
        scored = []

        for item in self.entries:
            score = 0
            keywords = [self._normalize(keyword) for keyword in item["keywords"]]
            text_blob = self._normalize(
                f"{item['title']} {item['description']} {' '.join(item['keywords'])}"
            )

            for term in query_terms:
                if len(term) < 3:
                    continue
                if term in keywords:
                    score += 3
                elif term in text_blob:
                    score += 1

            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    @staticmethod
    def _normalize(text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text.lower())
        return "".join(char for char in decomposed if not unicodedata.combining(char))

    def query_with_advice(self, query: str) -> str:
        """Generates a structured advice report for a query."""
        results = self.search(query, top_k=2)
        if not results:
            return "No se encontraron normativas directamente coincidentes en la base local."

        output_lines = [f"🛡️ **Resultados de Asesoría Defensiva (RAG)** para: *'{query}'*\n"]
        for r in results:
            output_lines.append(f"### [{r['framework']}] {r['title']}")
            output_lines.append(f"**Riesgo:** {r['description']}")
            output_lines.append(f"**Mitigación recomendada:** {r['mitigation']}\n")

        return "\n".join(output_lines)


rag_engine = RAGEngine()
