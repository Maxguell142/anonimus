import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.core.session import SessionManager


class TestSessionManager(unittest.TestCase):
    def test_messages_are_isolated_between_manager_sessions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "sessions.db"
            first = SessionManager(db_path)
            first.save_message("user", "ls")
            first.save_message("assistant", "old answer")

            second = SessionManager(db_path)
            second.save_message("user", "hola")

            self.assertEqual(
                [message["content"] for message in first.get_recent_messages()],
                ["ls", "old answer"],
            )
            self.assertEqual(
                [message["content"] for message in second.get_recent_messages()],
                ["hola"],
            )

    def test_existing_messages_table_is_migrated_without_leaking_legacy_history(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "legacy.db"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    "CREATE TABLE messages ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "role TEXT NOT NULL, content TEXT NOT NULL, "
                    "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
                )
                conn.execute(
                    "INSERT INTO messages (role, content) VALUES (?, ?)",
                    ("user", "old conversation"),
                )
                conn.commit()
            finally:
                conn.close()

            manager = SessionManager(db_path)
            self.assertEqual(manager.get_recent_messages(), [])

            manager.save_message("user", "new conversation")
            self.assertEqual(
                [message["content"] for message in manager.get_recent_messages()],
                ["new conversation"],
            )


if __name__ == "__main__":
    unittest.main()
