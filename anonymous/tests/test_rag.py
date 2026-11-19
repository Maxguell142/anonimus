import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from RAG.knowledge_base import KNOWLEDGE_ENTRIES
from anonymous.engines.blue.rag_engine import RAGEngine


class TestRagEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.documents_dir = self.root / "documents"
        self.documents_dir.mkdir()
        self.cache_path = self.root / "index.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_engine(self):
        return RAGEngine(
            entries=KNOWLEDGE_ENTRIES,
            documents_dir=self.documents_dir,
            cache_path=self.cache_path,
        )

    def test_unknown_query_does_not_invent_matches(self):
        engine = self.make_engine()
        results = engine.search("xyzzyfoobarbaz quantum banana", top_k=2)
        self.assertEqual(results, [])
        advice = engine.query_with_advice("xyzzyfoobarbaz quantum banana")
        self.assertIn("No se encontraron", advice)

    def test_sql_injection_hits_owasp(self):
        engine = self.make_engine()
        results = engine.search("inyeccion sql", top_k=2)
        self.assertTrue(results)
        self.assertTrue(any("OWASP" in r["framework"] for r in results))

    def test_new_topics_match_local_framework_entries(self):
        engine = self.make_engine()
        expected_frameworks = {
            "fuerza bruta": "OWASP Top 10",
            "ssrf": "OWASP Top 10",
            "parches": "CIS Controls v8",
            "registro de eventos": "NIST CSF 2.0",
        }
        for query, framework in expected_frameworks.items():
            with self.subTest(query=query):
                results = engine.search(query, top_k=3)
                self.assertTrue(results)
                self.assertTrue(any(item["framework"] == framework for item in results))

    def test_searches_added_markdown_and_returns_source(self):
        document = self.documents_dir / "networking" / "firewall.md"
        document.parent.mkdir()
        document.write_text(
            "# Firewall monitoring\n\n"
            "Network intrusion detection requires firewall telemetry and centralized logs.",
            encoding="utf-8",
        )

        results = self.make_engine().search("intrusion detection firewall telemetry")

        self.assertTrue(results)
        self.assertEqual(results[0]["source"], "networking\\firewall.md")
        self.assertIn("firewall telemetry", results[0]["description"])

    def test_new_document_invalidates_cache_without_restart(self):
        engine = self.make_engine()
        self.assertEqual(engine.search("wireless handshake authentication"), [])

        (self.documents_dir / "wifi.txt").write_text(
            "Wireless authentication uses a protected handshake.",
            encoding="utf-8",
        )

        results = engine.search("wireless authentication handshake")
        self.assertTrue(any(item.get("source") == "wifi.txt" for item in results))

    def test_pdf_results_include_page_reference(self):
        from io import BytesIO
        from unittest.mock import Mock, patch
        from pypdf import PdfWriter

        output = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        writer.write(output)
        (self.documents_dir / "network.pdf").write_bytes(output.getvalue())
        reader = Mock(
            is_encrypted=False,
            pages=[Mock(extract_text=Mock(return_value="Network firewall monitoring"))],
        )

        with patch("pypdf.PdfReader", return_value=reader):
            results = self.make_engine().search("network firewall monitoring")

        self.assertTrue(
            any(item.get("source") == "network.pdf" and item["page"] == 1 for item in results)
        )

    def test_reports_documents_without_extractable_text(self):
        from io import BytesIO
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        output = BytesIO()
        writer.write(output)
        (self.documents_dir / "scanned.pdf").write_bytes(output.getvalue())
        engine = self.make_engine()

        response = engine.query_with_advice("unknown topic with no matches")

        self.assertIn("Documentos omitidos", response)
        self.assertIn("scanned.pdf", response)


if __name__ == "__main__":
    unittest.main()
