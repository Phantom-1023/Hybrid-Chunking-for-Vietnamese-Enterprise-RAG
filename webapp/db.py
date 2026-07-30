"""SQLite persistence and ACL-first document access."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'member')),
    department_id INTEGER REFERENCES departments(id),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    access_scope TEXT NOT NULL CHECK(access_scope IN ('organization', 'department', 'private')),
    department_id INTEGER REFERENCES departments(id),
    owner_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    outcome TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def query_all(self, sql: str, parameters=()) -> list[dict]:
        with self.connect() as connection:
            return [
                dict(row) for row in connection.execute(sql, parameters).fetchall()
            ]

    def query_one(self, sql: str, parameters=()) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(sql, parameters).fetchone()
            return dict(row) if row else None

    def execute(self, sql: str, parameters=()) -> int:
        with self.connect() as connection:
            cursor = connection.execute(sql, parameters)
            return int(cursor.lastrowid)

    def allowed_documents(self, user: dict) -> list[dict]:
        """Apply document ACL in SQL before any retrieval or reranking."""
        return self.query_all(
            """
            SELECT d.*, dep.name AS department_name
            FROM documents d
            LEFT JOIN departments dep ON dep.id = d.department_id
            WHERE d.access_scope = 'organization'
               OR d.owner_id = ?
               OR (
                    d.access_scope = 'department'
                    AND d.department_id IS NOT NULL
                    AND d.department_id = ?
               )
               OR ? = 'admin'
            ORDER BY d.id
            """,
            (user["id"], user["department_id"], user["role"]),
        )

    def audit(
        self,
        *,
        user_id: int | None,
        action: str,
        resource_type: str,
        resource_id: str = "",
        outcome: str,
        detail: str = "",
    ) -> None:
        self.execute(
            """
            INSERT INTO audit_log
                (user_id, action, resource_type, resource_id, outcome, detail)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, action, resource_type, resource_id, outcome, detail[:500]),
        )
