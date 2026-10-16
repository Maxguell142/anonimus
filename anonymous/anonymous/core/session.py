"""
Session & Persistent Memory Manager for Anonymous.
Uses SQLite to store conversations, discovered findings, and PTT states.
"""

import sqlite3
import json
import uuid
from contextlib import closing
from datetime import datetime
from typing import List, Dict, Any, Optional
from anonymous.config import DB_PATH


class SessionManager:
    """Manages persistent state in SQLite database."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.session_id = str(uuid.uuid4())
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            # Chat messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            columns = {
                row["name"] for row in cursor.execute("PRAGMA table_info(messages)")
            }
            if "session_id" not in columns:
                cursor.execute("ALTER TABLE messages ADD COLUMN session_id TEXT")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_session_id_id "
                "ON messages (session_id, id)"
            )
            # Discovered findings (ports, vulns, compliance notes)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    details TEXT,
                    severity TEXT DEFAULT 'INFO',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # PTT (Pentest Task Tree) tasks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ptt_tasks (
                    id TEXT PRIMARY KEY,
                    phase TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    details TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_message(self, role: str, content: str):
        with closing(self._get_connection()) as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (self.session_id, role, content),
            )
            conn.commit()

    def get_recent_messages(self, limit: int = 15) -> List[Dict[str, Any]]:
        with closing(self._get_connection()) as conn:
            cursor = conn.execute(
                "SELECT role, content, created_at FROM messages "
                "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (self.session_id, limit),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in reversed(rows)]

    def record_finding(self, target: str, category: str, title: str, details: str = "", severity: str = "INFO"):
        with closing(self._get_connection()) as conn:
            conn.execute(
                "INSERT INTO findings (target, category, title, details, severity) VALUES (?, ?, ?, ?, ?)",
                (target, category, title, details, severity),
            )
            conn.commit()

    def count_findings(self) -> int:
        with closing(self._get_connection()) as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM findings").fetchone()
            return int(row["n"] if row else 0)

    def get_findings(self, limit: int = 20) -> List[Dict[str, Any]]:
        with closing(self._get_connection()) as conn:
            cursor = conn.execute(
                "SELECT target, category, title, details, severity, created_at FROM findings ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def update_task(self, task_id: str, phase: str, name: str, status: str, details: str = ""):
        with closing(self._get_connection()) as conn:
            conn.execute(
                """
                INSERT INTO ptt_tasks (id, phase, name, status, details, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    phase = excluded.phase,
                    name = excluded.name,
                    status = excluded.status,
                    details = excluded.details,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (task_id, phase, name, status, details),
            )
            conn.commit()

    def get_ptt_tasks(self) -> List[Dict[str, Any]]:
        with closing(self._get_connection()) as conn:
            cursor = conn.execute(
                "SELECT id, phase, name, status, details, updated_at FROM ptt_tasks ORDER BY phase, id"
            )
            return [dict(r) for r in cursor.fetchall()]


session_manager = SessionManager()
