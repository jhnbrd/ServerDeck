"""Optional local database seeder (copy to seed_local.py and customize)."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.data_store import DataStore, DataStoreError  # noqa: E402

# Copy this file to seed_local.py and replace with your own project definitions.
LOCAL_PROJECTS: list[dict] = [
    {
        "id": "my-backend",
        "name": "My Backend",
        "path": r"C:\path\to\project",
        "port": 8000,
        "icon": "",
        "command": r"python -m uvicorn main:app --host 0.0.0.0 --port 8000",
        "status": "ready",
    },
]


def seed(force: bool = False) -> None:
    store = DataStore()
    existing = store.get_active_projects()

    if existing and not force:
        print(f"Database already has {len(existing)} project(s). Use --force to replace them.")
        return

    if force and existing:
        for project in existing:
            store.archive_project(project["id"])
        print(f"Archived {len(existing)} existing project(s).")

    for project in LOCAL_PROJECTS:
        store.add_project(project)
        print(f"  + {project['name']} (:{project['port']})")

    print(f"\nSeeded {len(LOCAL_PROJECTS)} project(s) into serverdeck.db")


if __name__ == "__main__":
    try:
        seed(force="--force" in sys.argv)
    except DataStoreError as exc:
        print(f"Seeding failed: {exc}", file=sys.stderr)
        sys.exit(1)
