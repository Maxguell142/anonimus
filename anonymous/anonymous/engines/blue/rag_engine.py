"""Compatibility entrypoint; all RAG logic lives in the top-level RAG package."""

from RAG.engine import RAGEngine
from RAG.knowledge_base import KNOWLEDGE_ENTRIES

rag_engine = RAGEngine(KNOWLEDGE_ENTRIES)

__all__ = ["RAGEngine", "rag_engine"]
