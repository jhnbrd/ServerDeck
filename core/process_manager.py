"""Asynchronous process lifecycle management with recursive tree teardown."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover - runtime dependency
    psutil = None  # type: ignore[assignment]

from core.port_checker import evaluate_port_state, is_port_in_use


LogCallback = Callable[[str, str], None]


@dataclass
class ManagedProcess:
    project_id: str
    pid: int
    popen: subprocess.Popen[Any]
    started_at: float = field(default_factory=time.time)


class ProcessManager:
    """Tracks spawned applications and streams stdout/stderr off the UI thread."""

    def __init__(self, on_log: LogCallback | None = None) -> None:
        self._processes: dict[str, ManagedProcess] = {}
        self._log_buffers: dict[str, list[str]] = {}
        self._lock = threading.Lock()
        self._on_log = on_log or (lambda _project_id, _line: None)
        self._reader_threads: dict[str, threading.Thread] = {}

    def is_running(self, project_id: str) -> bool:
        with self._lock:
            managed = self._processes.get(project_id)
            if not managed:
                return False
            return self._alive(managed.pid)

    def get_pid(self, project_id: str) -> int | None:
        with self._lock:
            managed = self._processes.get(project_id)
            return managed.pid if managed and self._alive(managed.pid) else None

    def get_status(self, project_id: str, port: int) -> str:
        running = self.is_running(project_id)
        if running:
            return "active"
        return evaluate_port_state(port, False)

    def get_log_history(self, project_id: str) -> list[str]:
        with self._lock:
            return list(self._log_buffers.get(project_id, []))

    def start(
        self,
        project_id: str,
        name: str,
        cwd: str,
        command: str,
        port: int,
    ) -> tuple[bool, str]:
        if self.is_running(project_id):
            return False, f"{name} is already running."

        if is_port_in_use(port):
            return False, f"Port {port} is already in use."

        if not command.strip():
            return False, "Launch command is empty."

        if not os.path.isdir(cwd):
            return False, f"Project directory not found: {cwd}"

        shell = os.name == "nt"
        try:
            popen = subprocess.Popen(
                command,
                cwd=cwd,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except OSError as exc:
            return False, str(exc)

        managed = ManagedProcess(project_id=project_id, pid=popen.pid, popen=popen)
        with self._lock:
            self._processes[project_id] = managed
            self._log_buffers[project_id] = []

        reader = threading.Thread(
            target=self._stream_output,
            args=(project_id, popen),
            daemon=True,
            name=f"log-{project_id}",
        )
        self._reader_threads[project_id] = reader
        reader.start()
        return True, f"{name} started. PID {popen.pid}."

    def stop(self, project_id: str, name: str = "Application") -> tuple[bool, str]:
        with self._lock:
            managed = self._processes.get(project_id)
            if not managed:
                return False, f"{name} is not running."

        self._terminate_tree(managed.pid)
        try:
            managed.popen.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                managed.popen.kill()
            except OSError:
                pass

        with self._lock:
            self._processes.pop(project_id, None)
            self._reader_threads.pop(project_id, None)

        return True, f"{name} stopped."

    def stop_on_port(self, port: int, name: str = "Application") -> tuple[bool, str]:
        """Stop an untracked process that is listening on the given port."""
        if not is_port_in_use(port):
            return False, f"{name} is not running on port {port}."

        pid = self._find_listener_pid(port)
        if not pid:
            return False, f"Port {port} is in use but the owning process could not be identified."

        self._terminate_tree(pid)
        return True, f"{name} stopped (freed port {port})."

    def stop_all(self) -> list[str]:
        messages: list[str] = []
        with self._lock:
            ids = list(self._processes.keys())
        for project_id in ids:
            ok, message = self.stop(project_id)
            if message:
                messages.append(message)
            if not ok and message:
                continue
        return messages

    def stop_all_projects(self, projects: list[dict]) -> list[str]:
        """Stop tracked apps, then free configured ports held by orphaned processes."""
        messages = self.stop_all()
        freed_ports: set[int] = set()

        for project in projects:
            project_id = project.get("id", "")
            name = project.get("name", "Application")
            port = int(project.get("port", 0))
            if port <= 0 or port in freed_ports:
                continue
            if self.is_running(project_id):
                continue
            if not is_port_in_use(port):
                continue

            ok, message = self.stop_on_port(port, name)
            if message:
                messages.append(message)
            if ok:
                freed_ports.add(port)

        return messages

    def refresh_external_exits(self) -> list[str]:
        """Return project IDs whose processes ended outside ServerDeck."""
        ended: list[str] = []
        with self._lock:
            for project_id, managed in list(self._processes.items()):
                if not self._alive(managed.pid):
                    ended.append(project_id)
                    self._processes.pop(project_id, None)
                    self._reader_threads.pop(project_id, None)
        return ended

    def _stream_output(self, project_id: str, popen: subprocess.Popen[Any]) -> None:
        if popen.stdout is None:
            return
        for line in iter(popen.stdout.readline, ""):
            if not line:
                break
            self._record_log(project_id, line.rstrip("\n"))
        popen.stdout.close()

    def _record_log(self, project_id: str, line: str) -> None:
        with self._lock:
            self._log_buffers.setdefault(project_id, []).append(line)
        self._on_log(project_id, line)

    @staticmethod
    def _alive(pid: int) -> bool:
        if psutil is None:
            try:
                os.kill(pid, 0)
            except OSError:
                return False
            return True
        try:
            proc = psutil.Process(pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def _terminate_tree(self, root_pid: int) -> None:
        if psutil is None:
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(root_pid), "/T", "/F"],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                else:
                    os.kill(root_pid, signal.SIGTERM)
            except OSError:
                pass
            return

        try:
            root = psutil.Process(root_pid)
        except psutil.NoSuchProcess:
            return

        children = root.children(recursive=True)
        for child in reversed(children):
            try:
                child.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        gone, alive = psutil.wait_procs(children, timeout=2)
        for proc in alive:
            try:
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        try:
            root.terminate()
            root.wait(timeout=2)
        except psutil.TimeoutExpired:
            try:
                root.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    @staticmethod
    def _find_listener_pid(port: int) -> int | None:
        if psutil is None or port <= 0:
            return None
        for conn in psutil.net_connections(kind="inet"):
            if conn.status != psutil.CONN_LISTEN:
                continue
            laddr = conn.laddr
            if laddr and laddr.port == port and conn.pid:
                return conn.pid
        return None
