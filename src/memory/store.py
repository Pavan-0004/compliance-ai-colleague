import json
import sqlite3
import time
from pathlib import Path
from typing import List

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "memory.db"


class MemoryStore:
    """All notes/action items and their embeddings stay in a local SQLite
    file under data/ — never synced anywhere."""

    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                kind TEXT NOT NULL,
                embedding TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        self.conn.commit()

    def add_note(self, text: str, embedding: List[float], kind: str = "note"):
        self.conn.execute(
            "INSERT INTO notes (text, kind, embedding, created_at) VALUES (?, ?, ?, ?)",
            (text, kind, json.dumps(embedding), time.time()),
        )
        self.conn.commit()

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]

    def all_notes(self) -> List[dict]:
        rows = self.conn.execute(
            "SELECT id, text, kind, embedding, created_at FROM notes"
        ).fetchall()
        return [
            {"id": r[0], "text": r[1], "kind": r[2], "embedding": json.loads(r[3]), "created_at": r[4]}
            for r in rows
        ]

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[str]:
        from .embeddings import top_similar

        return top_similar(query_embedding, self.all_notes(), top_k)
