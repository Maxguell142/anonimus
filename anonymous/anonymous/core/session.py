"""
Session & Persistent Memory Manager for Anonymous.
Uses SQLite to store conversations, discovered findings, and PTT states.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from anonymous.config import DB_PATH


class SessionManager:
    """Manages persistent state in SQLite database."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Chat messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
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
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)",
                (role, content),
            )
            conn.commit()

    def get_recent_messages(self, limit: int = 15) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT role, content, created_at FROM messages ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in reversed(rows)]

    def record_finding(self, target: str, category: str, title: str, details: str = "", severity: str = "INFO"):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO findings (target, category, title, details, severity) VALUES (?, ?, ?, ?, ?)",
                (target, category, title, details, severity),
            )
            conn.commit()

    def get_findings(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT target, category, title, details, severity, created_at FROM findings ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def update_task(self, task_id: str, phase: str, name: str, status: str, details: str = ""):
        with self._get_connection() as conn:
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
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, phase, name, status, details, updated_at FROM ptt_tasks ORDER BY phase, id"
            )
            return [dict(r) for r in cursor.fetchall()]


session_manager = SessionManager()
