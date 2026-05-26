"""SQLite persistence for ServerDeck project definitions."""

from __future__ import annotations

import os
import sqlite3
import threading
import time
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

DEFAULT_PROJECT: dict[str, Any] = {
    "id": "",
    "name": "Untitled Application",
    "path": "",
    "port": 8000,
    "icon": "",
    "command": "",
    "status": "ready",
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    path        TEXT NOT NULL DEFAULT '',
    port        INTEGER NOT NULL DEFAULT 8000,
    icon        TEXT NOT NULL DEFAULT '',
    command     TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'ready',
    archived    INTEGER NOT NULL DEFAULT 0,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""

T = TypeVar("T")


class DataStoreError(Exception):
    """Raised when the SQLite database cannot be read or written."""


class DataStore:
    """Thread-safe read/write access to the ServerDeck SQLite database."""

    def __init__(self, db_path: str | None = None) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = db_path or os.path.join(base_dir, "serverdeck.db")
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as exc:
            raise DataStoreError(f"Unable to open database at {self.db_path}: {exc}") from exc

    def _init_db(self) -> None:
        db_dir = os.path.dirname(os.path.abspath(self.db_path)) or "."
        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError as exc:
            raise DataStoreError(f"Unable to create database directory '{db_dir}': {exc}") from exc

        with self._lock:
            try:
                self._create_schema()
            except sqlite3.DatabaseError as exc:
                if os.path.isfile(self.db_path):
                    self._quarantine_corrupt_db()
                    self._create_schema()
                else:
                    raise DataStoreError(f"Database initialization failed: {exc}") from exc
            except sqlite3.Error as exc:
                raise DataStoreError(f"Database initialization failed: {exc}") from exc

    def _quarantine_corrupt_db(self) -> None:
        stamp = int(time.time())
        backup_path = f"{self.db_path}.corrupt.{stamp}"
        try:
            os.replace(self.db_path, backup_path)
        except OSError as exc:
            raise DataStoreError(
                f"Database file appears corrupt and could not be quarantined: {exc}"
            ) from exc

    def _create_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
            conn.commit()

    def _run(self, operation: Callable[[], T], action: str) -> T:
        try:
            return operation()
        except DataStoreError:
            raise
        except sqlite3.IntegrityError as exc:
            raise DataStoreError(f"{action}: a record with that identifier already exists.") from exc
        except sqlite3.OperationalError as exc:
            message = str(exc).lower()
            if "locked" in message:
                raise DataStoreError(f"{action}: database is busy. Please try again.") from exc
            raise DataStoreError(f"{action}: {exc}") from exc
        except sqlite3.Error as exc:
            raise DataStoreError(f"{action}: {exc}") from exc

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _normalize_project(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            return deepcopy(DEFAULT_PROJECT)

        normalized = deepcopy(DEFAULT_PROJECT)
        for key, default in DEFAULT_PROJECT.items():
            value = item.get(key, default)
            if key == "port":
                try:
                    normalized[key] = int(value)
                except (TypeError, ValueError):
                    normalized[key] = default
            elif key == "name" and value:
                normalized[key] = str(value)
            elif value is not None:
                normalized[key] = value if isinstance(value, type(default)) else str(value)
        if not normalized["id"]:
            normalized["id"] = self._generate_id(normalized["name"])
        return normalized

    @staticmethod
    def _generate_id(name: str) -> str:
        slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
        slug = slug[:32] or "project"
        return f"{slug}-{uuid.uuid4().hex[:8]}"

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "path": row["path"],
            "port": row["port"],
            "icon": row["icon"],
            "command": row["command"],
            "status": row["status"],
        }

    def _fetch_projects(self, archived: bool) -> list[dict[str, Any]]:
        flag = 1 if archived else 0

        def query() -> list[dict[str, Any]]:
            with self._lock:
                with self._connect() as conn:
                    rows = conn.execute(
                        """
                        SELECT id, name, path, port, icon, command, status
                        FROM projects
                        WHERE archived = ?
                        ORDER BY sort_order, name
                        """,
                        (flag,),
                    ).fetchall()
            return [self._row_to_dict(row) for row in rows]

        return self._run(query, "Loading projects")

    def get_active_projects(self) -> list[dict[str, Any]]:
        return self._fetch_projects(archived=False)

    def get_archived_projects(self) -> list[dict[str, Any]]:
        return self._fetch_projects(archived=True)

    def add_project(self, project: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_project(project)
        now = self._now()

        def insert() -> dict[str, Any]:
            with self._lock:
                with self._connect() as conn:
                    max_order = conn.execute(
                        "SELECT COALESCE(MAX(sort_order), -1) FROM projects"
                    ).fetchone()[0]
                    conn.execute(
                        """
                        INSERT INTO projects
                            (id, name, path, port, icon, command, status, archived, sort_order, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                        """,
                        (
                            normalized["id"],
                            normalized["name"],
                            normalized["path"],
                            normalized["port"],
                            normalized["icon"],
                            normalized["command"],
                            normalized.get("status", "ready"),
                            max_order + 1,
                            now,
                            now,
                        ),
                    )
                    conn.commit()
            return normalized

        return self._run(insert, "Adding project")

    def update_project(self, project_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.find_project(project_id)
        if not existing:
            return None

        merged = self._normalize_project({**existing, **updates, "id": project_id})
        now = self._now()

        def update() -> dict[str, Any]:
            with self._lock:
                with self._connect() as conn:
                    conn.execute(
                        """
                        UPDATE projects
                        SET name = ?, path = ?, port = ?, icon = ?, command = ?, status = ?, updated_at = ?
                        WHERE id = ? AND archived = 0
                        """,
                        (
                            merged["name"],
                            merged["path"],
                            merged["port"],
                            merged["icon"],
                            merged["command"],
                            merged.get("status", "ready"),
                            now,
                            project_id,
                        ),
                    )
                    conn.commit()
            return merged

        return self._run(update, "Updating project")

    def archive_project(self, project_id: str) -> bool:
        now = self._now()

        def archive() -> bool:
            with self._lock:
                with self._connect() as conn:
                    cursor = conn.execute(
                        """
                        UPDATE projects
                        SET archived = 1, status = 'ready', updated_at = ?
                        WHERE id = ? AND archived = 0
                        """,
                        (now, project_id),
                    )
                    conn.commit()
                    return cursor.rowcount > 0

        return self._run(archive, "Archiving project")

    def find_project(self, project_id: str) -> dict[str, Any] | None:
        def query() -> dict[str, Any] | None:
            with self._lock:
                with self._connect() as conn:
                    row = conn.execute(
                        """
                        SELECT id, name, path, port, icon, command, status
                        FROM projects
                        WHERE id = ? AND archived = 0
                        """,
                        (project_id,),
                    ).fetchone()
            return self._row_to_dict(row) if row else None

        return self._run(query, "Finding project")
