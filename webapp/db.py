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
CREATE TABLE IF NOT EXISTS department_memberships (
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'member' CHECK(role IN ('manager', 'member')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (department_id, user_id)
);
CREATE TABLE IF NOT EXISTS document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    locator TEXT NOT NULL DEFAULT '',
    chunk_index INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS document_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL DEFAULT '#596780',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS document_label_links (
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    label_id INTEGER NOT NULL REFERENCES document_labels(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, label_id)
);
CREATE TABLE IF NOT EXISTS document_access_grants (
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (document_id, user_id)
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
            self._ensure_document_columns(connection)
            connection.execute(
                """
                INSERT INTO document_chunks (document_id, content, locator, chunk_index)
                SELECT d.id, d.content, 'Nội dung cũ', 0
                FROM documents d
                WHERE d.content <> ''
                  AND NOT EXISTS (
                    SELECT 1 FROM document_chunks c WHERE c.document_id = d.id
                  )
                """
            )

    @staticmethod
    def _ensure_document_columns(connection: sqlite3.Connection) -> None:
        existing = {row["name"] for row in connection.execute("PRAGMA table_info(documents)")}
        additions = {
            "source_name": "TEXT NOT NULL DEFAULT ''",
            "mime_type": "TEXT NOT NULL DEFAULT 'text/plain'",
            "storage_path": "TEXT NOT NULL DEFAULT ''",
            "processing_status": "TEXT NOT NULL DEFAULT 'ready'",
            "checksum": "TEXT NOT NULL DEFAULT ''",
            "updated_at": "TEXT NOT NULL DEFAULT ''",
        }
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(f"ALTER TABLE documents ADD COLUMN {name} {definition}")

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

    def execute_count(self, sql: str, parameters=()) -> int:
        with self.connect() as connection:
            cursor = connection.execute(sql, parameters)
            return int(cursor.rowcount)

    def allowed_documents(self, user: dict) -> list[dict]:
        """Apply document ACL in SQL before any retrieval or reranking."""
        department_ids = list(user.get("department_ids", []))
        if user["department_id"] is not None:
            department_ids.append(user["department_id"])
        department_ids = list(dict.fromkeys(department_ids))
        clauses = ["d.access_scope = 'organization'", "d.owner_id = ?", "(d.access_scope = 'private' AND g.user_id = ?)"]
        params: list[object] = [user["id"], user["id"]]
        if user["role"] == "admin":
            clauses.append("? = 'admin'")
            params.append("admin")
        elif department_ids:
            placeholders = ",".join("?" for _ in department_ids)
            clauses.append(f"(d.access_scope = 'department' AND d.department_id IN ({placeholders}))")
            params.extend(department_ids)
        return self.query_all(
            f"""
            SELECT d.*, dep.name AS department_name
            FROM documents d
            LEFT JOIN departments dep ON dep.id = d.department_id
            LEFT JOIN document_access_grants g
              ON g.document_id = d.id AND g.user_id = ?
            WHERE ({' OR '.join(clauses)})
            ORDER BY d.id
            """,
            (user["id"], *params),
        )

    def allowed_document_chunks(self, user: dict) -> list[dict]:
        """Return chunks only after the document-level ACL predicate is applied."""
        managed_ids = user.get("managed_department_ids", [])
        department_ids = user.get("department_ids", [])
        if user["department_id"] is not None:
            department_ids = [*department_ids, user["department_id"]]
        department_ids = list(dict.fromkeys(department_ids))
        clauses = ["d.access_scope = 'organization'", "d.owner_id = ?", "d.access_scope = 'private' AND g.user_id = ?"]
        params: list[object] = [user["id"], user["id"]]
        if user["role"] == "admin":
            clauses.append("? = 'admin'")
            params.append("admin")
        elif department_ids:
            placeholders = ",".join("?" for _ in department_ids)
            clauses.append(
                f"(d.access_scope = 'department' AND d.department_id IN ({placeholders}))"
            )
            params.extend(department_ids)
        return self.query_all(
            f"""
            SELECT c.id, c.document_id, c.content, c.locator, c.chunk_index,
                   d.title, d.source_name, d.access_scope, d.department_id,
                   dep.name AS department_name
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            LEFT JOIN departments dep ON dep.id = d.department_id
            LEFT JOIN document_access_grants g
              ON g.document_id = d.id AND g.user_id = ?
            WHERE ({' OR '.join(clauses)})
            ORDER BY c.document_id, c.chunk_index
            """,
            (user["id"], *params),
        )

    def department_ids_for_user(self, user_id: int) -> list[int]:
        return [
            int(row["department_id"])
            for row in self.query_all(
                "SELECT department_id FROM department_memberships WHERE user_id = ?",
                (user_id,),
            )
        ]

    def managed_department_ids_for_user(self, user_id: int) -> list[int]:
        return [
            int(row["department_id"])
            for row in self.query_all(
                "SELECT department_id FROM department_memberships WHERE user_id = ? AND role = 'manager'",
                (user_id,),
            )
        ]

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
