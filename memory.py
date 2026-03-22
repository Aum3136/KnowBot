from sqlalchemy import create_engine, text
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class ChatMemory:
    def __init__(self):
        db_url = os.getenv("SUPABASE_DB_URL")
        self.engine = create_engine(db_url)
        self._create_table()
        print("[MEMORY] Connected to PostgreSQL — chat history enabled!")

    def _create_table(self):
        """Create chat_messages table if it doesn't exist."""
        with self.engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    project_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_session_id 
                ON chat_messages(session_id);
            """))

    def add_message(self, session_id: str, role: str, content: str, project_id: str = None):
        """Save a single message to the database."""
        with self.engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO chat_messages (session_id, role, content, project_id)
                    VALUES (:session_id, :role, :content, :project_id)
                """),
                {
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "project_id": project_id
                }
            )

    def get_recent_messages(self, session_id: str, limit: int = 10) -> List[dict]:
        """Get last N messages for a session."""
        with self.engine.begin() as conn:
            rows = conn.execute(
                text("""
                    SELECT role, content FROM chat_messages
                    WHERE session_id = :session_id
                    ORDER BY created_at ASC
                    LIMIT :limit
                """),
                {"session_id": session_id, "limit": limit}
            ).fetchall()
        return [{"role": row.role, "content": row.content} for row in rows]

    def clear_session(self, session_id: str):
        """Clear all messages for a session."""
        with self.engine.begin() as conn:
            conn.execute(
                text("DELETE FROM chat_messages WHERE session_id = :session_id"),
                {"session_id": session_id}
            )
        print(f"[MEMORY] Cleared session: {session_id}")

    def get_session_count(self, session_id: str) -> int:
        """Get number of messages in a session."""
        with self.engine.begin() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM chat_messages WHERE session_id = :session_id"),
                {"session_id": session_id}
            ).scalar()
        return result

# Singleton instance
chat_memory = ChatMemory()