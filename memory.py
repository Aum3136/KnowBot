import sqlite3
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "chat_history.db"

class ChatMemory:
    def __init__(self):
        try:
            self.db_path = DB_PATH
            self._create_table()
            self.enabled = True
            print("[MEMORY] SQLite chat history enabled!")
        except Exception as e:
            self.enabled = False
            print(f"[MEMORY] Warning: {e}")

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    project_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_id 
                ON chat_messages(session_id)
            """)

    def add_message(self, session_id: str, role: str, content: str, project_id: str = None):
        if not self.enabled:
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO chat_messages (session_id, role, content, project_id) VALUES (?, ?, ?, ?)",
                (session_id, role, content, project_id)
            )

    def get_recent_messages(self, session_id: str, limit: int = 10) -> List[dict]:
        if not self.enabled:
            return []
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT role, content FROM chat_messages
                   WHERE session_id = ?
                   ORDER BY created_at ASC
                   LIMIT ?""",
                (session_id, limit)
            ).fetchall()
        return [{"role": row[0], "content": row[1]} for row in rows]

    def clear_session(self, session_id: str):
        if not self.enabled:
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM chat_messages WHERE session_id = ?",
                (session_id,)
            )
        print(f"[MEMORY] Cleared session: {session_id}")

    def get_session_count(self, session_id: str) -> int:
        if not self.enabled:
            return 0
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM chat_messages WHERE session_id = ?",
                (session_id,)
            ).fetchone()
        return result[0]

# Singleton instance
chat_memory = ChatMemory()



