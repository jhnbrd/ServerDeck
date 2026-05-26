"""Application paths for development and packaged (PyInstaller) builds."""

from __future__ import annotations

import os
import sys

APP_NAME = "ServerDeck"
APP_VERSION = "1.0.0"


def is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def bundle_dir() -> str:
    if is_frozen():
        return getattr(sys, "_MEIPASS")
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def app_root() -> str:
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def user_data_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def default_db_path() -> str:
    if is_frozen():
        return os.path.join(user_data_dir(), "serverdeck.db")
    return os.path.join(app_root(), "serverdeck.db")
