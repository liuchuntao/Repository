from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import settings


class Database:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        schema = """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            companion_name TEXT NOT NULL,
            preferences_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS companion_state (
            user_id TEXT PRIMARY KEY,
            mood TEXT NOT NULL DEFAULT '平静',
            energy REAL NOT NULL DEFAULT 0.70,
            intimacy REAL NOT NULL DEFAULT 0.10,
            trust REAL NOT NULL DEFAULT 0.10,
            interaction_count INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            emotion_label TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_messages_user_session ON messages(user_id, session_id, id DESC);
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            importance REAL NOT NULL DEFAULT 0.5,
            source_message TEXT,
            access_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_accessed_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_memories_user_importance ON memories(user_id, importance DESC, id DESC);
        """
        with self._lock, self._connect() as conn:
            conn.executescript(schema)
            conn.commit()

    def ensure_user(self, user_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("INSERT OR IGNORE INTO users(user_id, companion_name) VALUES (?, ?)", (user_id, settings.companion_name))
            conn.execute("INSERT OR IGNORE INTO companion_state(user_id) VALUES (?)", (user_id,))
            conn.commit()

    def add_message(self, user_id: str, session_id: str, role: str, content: str, emotion_label: Optional[str] = None) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("INSERT INTO messages(user_id, session_id, role, content, emotion_label) VALUES (?, ?, ?, ?, ?)", (user_id, session_id, role, content, emotion_label))
            conn.commit()

    def get_recent_messages(self, user_id: str, session_id: str, limit: int) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT role, content, emotion_label, created_at FROM messages WHERE user_id = ? AND session_id = ? ORDER BY id DESC LIMIT ?", (user_id, session_id, limit)).fetchall()
        return [dict(row) for row in reversed(rows)]

    def add_memory(self, user_id: str, content: str, category: str, importance: float, source_message: str) -> bool:
        with self._lock, self._connect() as conn:
            duplicate = conn.execute("SELECT id FROM memories WHERE user_id = ? AND content = ? LIMIT 1", (user_id, content)).fetchone()
            if duplicate:
                return False
            conn.execute("INSERT INTO memories(user_id, content, category, importance, source_message) VALUES (?, ?, ?, ?, ?)", (user_id, content, category, importance, source_message))
            conn.commit()
            return True

    def search_memories(self, user_id: str, query_terms: List[str], limit: int) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT id, content, category, importance, access_count, created_at FROM memories WHERE user_id = ? ORDER BY importance DESC, id DESC LIMIT 80", (user_id,)).fetchall()
            scored = []
            for row in rows:
                item = dict(row)
                keyword_score = sum(1.0 for term in query_terms if term and term.lower() in item["content"].lower())
                item["_score"] = keyword_score * 1.5 + float(item["importance"])
                scored.append(item)
            scored.sort(key=lambda x: x["_score"], reverse=True)
            selected = scored[:limit]
            if selected:
                ids = [str(x["id"]) for x in selected]
                placeholders = ",".join("?" for _ in ids)
                conn.execute(f"UPDATE memories SET access_count = access_count + 1, last_accessed_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})", ids)
                conn.commit()
        for item in selected:
            item.pop("_score", None)
        return selected

    def get_state(self, user_id: str) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT mood, energy, intimacy, trust, interaction_count FROM companion_state WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            self.ensure_user(user_id)
            return self.get_state(user_id)
        return dict(row)

    def update_state(self, user_id: str, state: Dict[str, Any]) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("UPDATE companion_state SET mood = ?, energy = ?, intimacy = ?, trust = ?, interaction_count = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (state["mood"], state["energy"], state["intimacy"], state["trust"], state["interaction_count"], user_id))
            conn.commit()

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        self.ensure_user(user_id)
        with self._lock, self._connect() as conn:
            user = conn.execute("SELECT user_id, companion_name, preferences_json FROM users WHERE user_id = ?", (user_id,)).fetchone()
            memories = conn.execute("SELECT content, category, importance, created_at FROM memories WHERE user_id = ? ORDER BY id DESC LIMIT 20", (user_id,)).fetchall()
        return {"user_id": user["user_id"], "companion_name": user["companion_name"], "preferences": json.loads(user["preferences_json"] or "{}"), "state": self.get_state(user_id), "recent_memories": [dict(x) for x in memories]}


db = Database(settings.database_path)
