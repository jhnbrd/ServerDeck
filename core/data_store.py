"""SQLite persistence for ServerDeck project definitions."""

from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

DEFAULT_PROJECT: dict[str, Any] = {
    "id": "",
    "name": "Untitled Application",
    "path": "",
    "port": 8000,
    "icon": "",
    "command": "",
    "status": "ready",
}

SEED_PROJECTS: list[dict[str, Any]] = [
    {
        "id": "rapidresponse-backend",
        "name": "RapidResponse Backend",
        "path": r"D:\Projects\RapidResponse",
        "port": 8110,
        "icon": "",
        "command": r"call venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8110",
        "status": "ready",
    },
    {
        "id": "brewtracks-frontend",
        "name": "BrewTracks Frontend",
        "path": r"D:\Projects\BrewTracks All Versions\BrewTracks v5\backend\BrewTracks.Frontend",
        "port": 8201,
        "icon": "",
        "command": r"set PORT=8201 && npm run dev",
        "status": "ready",
    },
    {
        "id": "brewtracks-api",
        "name": "BrewTracks API",
        "path": r"D:\Projects\BrewTracks All Versions\BrewTracks v5\backend\BrewTracks.API",
        "port": 8200,
        "icon": "",
        "command": r"dotnet run --urls=http://0.0.0.0:8200",
        "status": "ready",
    },
    {
        "id": "brews-n-blooms-portal",
        "name": "Brews n Blooms Portal",
        "path": r"D:\Projects\BrewsAndBloomsPortal",
        "port": 8080,
        "icon": "",
        "command": r"php artisan serve --host=0.0.0.0 --port=8080",
        "status": "ready",
    },
]

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


class DataStore:
    """Thread-safe read/write access to the ServerDeck SQLite database."""

    def __init__(self, db_path: str | None = None) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = db_path or os.path.join(base_dir, "serverdeck.db")
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            with self._connect() as conn:
                conn.executescript(_SCHEMA)
                count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
                if count == 0:
                    now = self._now()
                    for order, project in enumerate(SEED_PROJECTS):
                        normalized = self._normalize_project(project)
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
                                normalized["status"],
                                order,
                                now,
                                now,
                            ),
                        )
                conn.commit()

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

    def get_active_projects(self) -> list[dict[str, Any]]:
        return self._fetch_projects(archived=False)

    def get_archived_projects(self) -> list[dict[str, Any]]:
        return self._fetch_projects(archived=True)

    def add_project(self, project: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_project(project)
        now = self._now()
        with self._lock:
            with self._connect() as conn:
                max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) FROM projects").fetchone()[0]
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

    def update_project(self, project_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.find_project(project_id)
        if not existing:
            return None

        merged = self._normalize_project({**existing, **updates, "id": project_id})
        now = self._now()
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

    def archive_project(self, project_id: str) -> bool:
        now = self._now()
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

    def find_project(self, project_id: str) -> dict[str, Any] | None:
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
