"""Local lexical RAG over curated entries and user-provided documents."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SUPPORTED_SUFFIXES = {".md", ".pdf", ".txt"}
CHUNK_WORDS = 700
CHUNK_OVERLAP = 100
CACHE_VERSION = 1
TOKEN_PATTERN = re.compile(r"[a-z0-9]{2,}", re.IGNORECASE)


class RAGEngine:
    """Search curated controls and locally stored document passages."""

    def __init__(
        self,
        entries: Optional[List[Dict[str, Any]]] = None,
        documents_dir: Optional[Path] = None,
        cache_path: Optional[Path] = None,
    ):
        from RAG.knowledge_base import KNOWLEDGE_ENTRIES

        self.entries = entries if entries is not None else KNOWLEDGE_ENTRIES
        self.documents_dir = documents_dir or Path(__file__).resolve().parent / "documents"
        self.cache_path = cache_path or Path.home() / ".anonymous" / "rag_documents_index.json"
        self._document_chunks: Optional[List[Dict[str, Any]]] = None
        self._document_tokens: Optional[List[List[str]]] = None
        self._document_warnings: List[str] = []
        self._fingerprint: Optional[List[Tuple[str, int, int]]] = None

    @staticmethod
    def _normalize(text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text.lower())
        ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
        return " ".join(TOKEN_PATTERN.findall(ascii_text))

    @classmethod
    def _tokens(cls, text: str) -> List[str]:
        return cls._normalize(text).split()

    def _source_files(self) -> List[Path]:
        if not self.documents_dir.exists():
            return []
        return sorted(
            (
                path for path in self.documents_dir.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
            ),
            key=lambda path: str(path).casefold(),
        )

    def _get_fingerprint(self, files: Iterable[Path]) -> List[Tuple[str, int, int]]:
        return [
            (
                str(path.relative_to(self.documents_dir)),
                path.stat().st_size,
                path.stat().st_mtime_ns,
            )
            for path in files
        ]

    def _load_document_index(self) -> List[Dict[str, Any]]:
        files = self._source_files()
        fingerprint = self._get_fingerprint(files)
        if self._document_chunks is not None and fingerprint == self._fingerprint:
            return self._document_chunks

        if self._document_chunks is None and self.cache_path.exists():
            try:
                cached = json.loads(self.cache_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"No se pudo leer el índice RAG {self.cache_path}: {exc}") from exc
            if not isinstance(cached, dict) or cached.get("version") != CACHE_VERSION:
                raise RuntimeError(
                    f"El índice RAG {self.cache_path} tiene un formato no compatible; "
                    "elimínalo para volver a generarlo."
                )
            cached_fingerprint = cached.get("fingerprint")
            if cached_fingerprint == [list(item) for item in fingerprint]:
                chunks = cached.get("chunks")
                warnings = cached.get("warnings", [])
                if not isinstance(chunks, list) or not isinstance(warnings, list):
                    raise RuntimeError(f"El índice RAG {self.cache_path} está dañado.")
                self._document_chunks = chunks
                self._document_tokens = [
                    self._tokens(document["description"]) for document in chunks
                ]
                self._document_warnings = warnings
                self._fingerprint = fingerprint
                return self._document_chunks

        chunks: List[Dict[str, Any]] = []
        warnings: List[str] = []
        for path in files:
            try:
                chunks.extend(self._extract_document(path))
            except (OSError, UnicodeError, ValueError) as exc:
                warnings.append(f"{path.name}: {exc}")

        self._write_cache(fingerprint, chunks, warnings)
        self._document_chunks = chunks
        self._document_tokens = [self._tokens(document["description"]) for document in chunks]
        self._document_warnings = warnings
        self._fingerprint = fingerprint
        return chunks

    def _extract_document(self, path: Path) -> List[Dict[str, Any]]:
        if path.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader
                from pypdf.errors import PdfReadError
            except ImportError as exc:
                raise RuntimeError(
                    "Falta pypdf para leer PDF. Instala las dependencias con "
                    "`python -m pip install -r requirements.txt`."
                ) from exc

            try:
                reader = PdfReader(str(path))
            except PdfReadError as exc:
                raise ValueError(f"PDF inválido: {exc}") from exc
            if reader.is_encrypted:
                raise ValueError("el PDF está cifrado y no se puede indexar sin contraseña.")
            try:
                pages = [
                    (index + 1, page.extract_text() or "")
                    for index, page in enumerate(reader.pages)
                ]
            except PdfReadError as exc:
                raise ValueError(f"no se pudo extraer el texto: {exc}") from exc
        else:
            pages = [(None, path.read_text(encoding="utf-8"))]

        chunks: List[Dict[str, Any]] = []
        for page_number, text in pages:
            words = text.split()
            if not words:
                continue
            start = 0
            while start < len(words):
                end = min(start + CHUNK_WORDS, len(words))
                passage = " ".join(words[start:end]).strip()
                if passage:
                    relative_path = path.relative_to(self.documents_dir)
                    page_label = f" (p. {page_number})" if page_number is not None else ""
                    chunks.append({
                        "id": f"doc:{relative_path}:{page_number or 0}:{start}",
                        "framework": "Documento local",
                        "title": path.stem,
                        "keywords": [],
                        "description": passage,
                        "mitigation": f"Fragmento referencial de {relative_path}{page_label}.",
                        "source": str(relative_path),
                        "page": page_number,
                    })
                if end == len(words):
                    break
                start = end - CHUNK_OVERLAP

        if not chunks:
            raise ValueError("no se encontró texto extraíble; si es un escaneo, aplica OCR primero.")
        return chunks

    def _write_cache(
        self,
        fingerprint: List[Tuple[str, int, int]],
        chunks: List[Dict[str, Any]],
        warnings: List[str],
    ) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
        payload = {
            "version": CACHE_VERSION,
            "fingerprint": [list(item) for item in fingerprint],
            "chunks": chunks,
            "warnings": warnings,
        }
        try:
            temporary_path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            temporary_path.replace(self.cache_path)
        except OSError as exc:
            raise RuntimeError(f"No se pudo guardar el índice RAG {self.cache_path}: {exc}") from exc

    @staticmethod
    def _bm25(query_tokens: List[str], document_tokens: List[str], average_length: float, document_count: int, frequencies: Counter) -> float:
        if not document_tokens or not query_tokens:
            return 0.0
        term_counts = Counter(document_tokens)
        length_ratio = len(document_tokens) / average_length if average_length else 0
        score = 0.0
        for term in set(query_tokens):
            term_frequency = term_counts[term]
            if not term_frequency:
                continue
            inverse_frequency = math.log(
                1 + (document_count - frequencies[term] + 0.5) / (frequencies[term] + 0.5)
            )
            score += inverse_frequency * (
                term_frequency * 2.5 / (term_frequency + 1.5 * (0.25 + 0.75 * length_ratio))
            )
        return score

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Return the highest-ranked matching passages with source locations."""
        if top_k <= 0 or not query.strip():
            return []
        query_tokens = self._tokens(query)
        if not query_tokens:
            return []

        documents = self._load_document_index()
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for item in self.entries:
            keywords = [self._normalize(keyword) for keyword in item.get("keywords", [])]
            text_blob = self._normalize(
                f"{item.get('title', '')} {item.get('description', '')} {' '.join(item.get('keywords', []))}"
            )
            score = sum(
                3 if term in keywords else 1 if term in text_blob else 0
                for term in set(query_tokens)
                if len(term) >= 3
            )
            if score:
                scored.append((float(score), {**item, "source": "Base local", "page": None}))

        all_tokens = self._document_tokens or [
            self._tokens(document["description"]) for document in documents
        ]
        document_count = len(all_tokens)
        average_length = sum(len(tokens) for tokens in all_tokens) / document_count if document_count else 0
        frequencies = Counter(
            token
            for tokens in all_tokens
            for token in set(tokens)
        )
        for document, tokens in zip(documents, all_tokens):
            score = self._bm25(query_tokens, tokens, average_length, document_count, frequencies)
            if score:
                scored.append((score, {key: value for key, value in document.items() if key != "tokens"}))

        scored.sort(key=lambda result: (-result[0], result[1].get("source", ""), result[1].get("title", "")))
        return [item for _, item in scored[:top_k]]

    def query_with_advice(self, query: str) -> str:
        """Format retrieved sources as a traceable local reference response."""
        results = self.search(query, top_k=3)
        if not results:
            message = "No se encontraron coincidencias en la base RAG local."
            if self._document_warnings:
                message += "\n\n**Documentos omitidos:** " + "; ".join(self._document_warnings)
            return message

        output_lines = [f"🛡️ **Resultados RAG** para: *'{query}'*\n"]
        for result in results:
            output_lines.append(f"### [{result.get('framework', 'Documento local')}] {result['title']}")
            output_lines.append(f"**Fuente:** {result.get('source', 'Base local')}"
                                + (f", página {result['page']}" if result.get("page") else ""))
            output_lines.append(f"**Contenido:** {result.get('description', '')}")
            if result.get("mitigation"):
                output_lines.append(f"**Nota:** {result['mitigation']}")
            output_lines.append("")
        if self._document_warnings:
            output_lines.append(
                "**Documentos omitidos:** " + "; ".join(self._document_warnings)
            )
        return "\n".join(output_lines)

    def document_status(self) -> Dict[str, Any]:
        """Return index counts and any documents that could not be extracted."""
        chunks = self._load_document_index()
        return {
            "documents_dir": str(self.documents_dir),
            "documents": len(self._fingerprint or []),
            "chunks": len(chunks),
            "warnings": list(self._document_warnings),
        }
