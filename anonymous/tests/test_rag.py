import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.engines.blue.rag_engine import RAGEngine


class TestRagEngine(unittest.TestCase):
    def test_unknown_query_does_not_invent_matches(self):
        engine = RAGEngine()
        results = engine.search("xyzzyfoobarbaz quantum banana", top_k=2)
        self.assertEqual(results, [])
        advice = engine.query_with_advice("xyzzyfoobarbaz quantum banana")
        self.assertIn("No se encontraron", advice)

    def test_sql_injection_hits_owasp(self):
        engine = RAGEngine()
        results = engine.search("inyeccion sql", top_k=2)
        self.assertTrue(results)
        self.assertTrue(any("OWASP" in r["framework"] for r in results))

    def test_new_topics_match_local_framework_entries(self):
        engine = RAGEngine()
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


if __name__ == "__main__":
    unittest.main()
