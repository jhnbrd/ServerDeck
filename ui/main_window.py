"""Primary ServerDeck dashboard window."""

from __future__ import annotations

import os
import subprocess
import threading
from tkinter import messagebox

import customtkinter as ctk

from core.data_store import DataStore, DataStoreError
from core.network_manager import apply_static_ip, list_adapters
from core.port_checker import evaluate_port_state, is_port_in_use
from core.process_manager import ProcessManager
from ui.components.app_row import AppRow
from ui.components.log_panel import LogPanel
from ui.components.network_panel import NetworkPanel
from ui.components.toolbar import Toolbar
from ui.modals.console_window import ConsoleWindow
from ui.modals.project_wizard import ProjectWizard
from ui.theme import (
    BG_CARD,
    BG_PRIMARY,
    FONT_FAMILY,
    TEXT_MUTED,
    TEXT_SECONDARY,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.maxsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.resizable(False, False)
        self.configure(fg_color=BG_PRIMARY)
        self._closing = False
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self.data_store = DataStore()
        self.console_windows: dict[str, ConsoleWindow] = {}
        self.app_rows: dict[str, AppRow] = {}

        self.process_manager = ProcessManager(on_log=self._on_process_log)

        root = ctk.CTkFrame(self, fg_color=BG_PRIMARY)
        root.pack(fill="both", expand=True, padx=10, pady=8)

        self.network_panel = NetworkPanel(root, on_apply=self._apply_network)
        self.network_panel.pack(fill="x", pady=(0, 6))

        self.toolbar = Toolbar(
            root,
            on_start_all=self._start_all_async,
            on_stop_all=self._stop_all_async,
            on_add=self._open_add_wizard,
        )
        self.toolbar.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            root,
            text="CONFIGURED APPLICATION INVENTORY",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.list_frame = ctk.CTkScrollableFrame(
            root,
            fg_color=BG_PRIMARY,
            height=150,
            scrollbar_button_color="#3A424A",
            scrollbar_button_hover_color="#0066CC",
        )
        self.list_frame.pack(fill="both", expand=True, pady=(0, 6))

        self.log_panel = LogPanel(root)
        self.log_panel.pack(fill="x")

        self._init_network()
        try:
            self._refresh_inventory()
        except DataStoreError as exc:
            self._log(str(exc), "warning")
            messagebox.showerror("Database Error", str(exc), parent=self)
        self._log("ServerDeck management engine loaded successfully.", "success")
        self._audit_ports()
        self.after(0, self._auto_startup_async)
        self.after(1000, self._heartbeat)

    def _show_empty_state(self) -> None:
        empty = ctk.CTkFrame(self.list_frame, fg_color=BG_CARD, corner_radius=8)
        empty.pack(fill="x", pady=3)
        ctk.CTkLabel(
            empty,
            text="No applications configured yet.",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(14, 4))
        ctk.CTkLabel(
            empty,
            text="Click  + Add New Application  to register your first local service.",
            font=(FONT_FAMILY, 10),
            text_color=TEXT_MUTED,
        ).pack(pady=(0, 14))

    def _init_network(self) -> None:
        try:
            adapters = list_adapters()
        except Exception as exc:
            self._log(f"Network adapter discovery failed: {exc}", "warning")
            adapters = []
        names = [adapter.name for adapter in adapters]
        primary = adapters[0] if adapters else None
        self.network_panel.set_adapters(names, primary.name if primary else None)
        if primary:
            self.network_panel.set_values(primary.ip, primary.subnet, primary.gateway)

    def _handle_db_error(self, action: str, exc: DataStoreError) -> None:
        message = f"{action}: {exc}"
        self._log(message, "warning")
        messagebox.showerror("Database Error", message, parent=self)

    def _refresh_inventory(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        self.app_rows.clear()

        projects = self.data_store.get_active_projects()
        if not projects:
            self._show_empty_state()
            self.toolbar.update_counts(0, 0)
            return

        for index, project in enumerate(projects):
            pid = project.get("id", "")
            status = self._resolve_status(project)
            project = {**project, "status": status}
            row = AppRow(
                self.list_frame,
                project=project,
                index=index,
                on_start=self._start_project_async,
                on_stop=self._stop_project_async,
                on_console=self._open_console,
                on_menu_action=self._menu_action,
            )
            row.pack(fill="x", pady=3)
            self.app_rows[pid] = row

        running = sum(1 for p in projects if self.process_manager.is_running(p.get("id", "")))
        self.toolbar.update_counts(running, len(projects))

    def _resolve_status(self, project: dict) -> str:
        project_id = project.get("id", "")
        port = int(project.get("port", 0))
        if self.process_manager.is_running(project_id):
            return "active"
        return evaluate_port_state(port, False)

    def _audit_ports(self) -> None:
        projects = self.data_store.get_active_projects()
        if not projects:
            self._log("No applications configured. Add a project to begin.", "info")
            return
        clear = 0
        conflicts = 0
        for project in projects:
            port = int(project.get("port", 0))
            pid = project.get("id", "")
            if self.process_manager.is_running(pid):
                continue
            state = evaluate_port_state(port, False)
            if state == "conflict":
                conflicts += 1
                self._log(
                    f"Alert: Port {port} collision detected. Please adjust application settings.",
                    "warning",
                )
                if pid in self.app_rows:
                    self.app_rows[pid].set_status("conflict")
            else:
                clear += 1
                if pid in self.app_rows:
                    self.app_rows[pid].set_status("ready")

        self._log(f"Port audit complete — {clear} ports clear, {conflicts} conflict detected.", "success")

    def _heartbeat(self) -> None:
        ended = self.process_manager.refresh_external_exits()
        for project_id in ended:
            project = self.data_store.find_project(project_id)
            name = project.get("name", "Application") if project else "Application"
            self._log(f"{name} process exited unexpectedly.", "warning")
            if project_id in self.app_rows and project:
                self.app_rows[project_id].set_status(
                    evaluate_port_state(int(project.get("port", 0)), False)
                )

        projects = self.data_store.get_active_projects()
        running = sum(1 for p in projects if self.process_manager.is_running(p.get("id", "")))
        self.toolbar.update_counts(running, len(projects))
        self.after(1000, self._heartbeat)

    def _log(self, message: str, level: str = "info") -> None:
        self.after(0, lambda: self.log_panel.append(message, level))

    def _on_process_log(self, project_id: str, line: str) -> None:
        window = self.console_windows.get(project_id)
        if window and window.winfo_exists():
            window.push_line(line)

    def _apply_network(self, adapter: str, ip: str, subnet: str, gateway: str, *, silent: bool = False) -> None:
        def task() -> None:
            ok, message = apply_static_ip(adapter, ip, subnet, gateway)
            level = "success" if ok else "warning"
            self._log(message, level)
            if silent:
                return
            if not ok:
                self.after(0, lambda: messagebox.showwarning("Network Configuration", message, parent=self))
            else:
                self.after(0, lambda: messagebox.showinfo("Network Configuration", message, parent=self))

        threading.Thread(target=task, daemon=True, name="apply-network").start()

    def _auto_startup_async(self) -> None:
        adapter, ip, subnet, gateway = self.network_panel.get_values()
        threading.Thread(
            target=self._auto_startup,
            args=(adapter, ip, subnet, gateway),
            daemon=True,
            name="auto-startup",
        ).start()

    def _auto_startup(self, adapter: str, ip: str, subnet: str, gateway: str) -> None:
        self._log("Auto-applying network settings...", "info")
        ok, message = apply_static_ip(adapter, ip, subnet, gateway)
        self._log(message, "success" if ok else "warning")
        if not ok:
            self._log("Continuing with Start All despite network configuration failure.", "warning")
        self._log("Auto-starting all configured applications...", "info")
        self._start_all()

    def _start_project_async(self, project_id: str) -> None:
        threading.Thread(
            target=self._start_project,
            args=(project_id,),
            daemon=True,
            name=f"start-{project_id}",
        ).start()

    def _start_project(self, project_id: str) -> None:
        project = self.data_store.find_project(project_id)
        if not project:
            return

        name = project.get("name", "Application")
        port = int(project.get("port", 0))
        if is_port_in_use(port) and not self.process_manager.is_running(project_id):
            self._log(f"Cannot start {name}: port {port} is in use.", "warning")
            self.after(0, lambda: self.app_rows[project_id].set_status("conflict"))
            return

        ok, message = self.process_manager.start(
            project_id=project_id,
            name=name,
            cwd=project.get("path", ""),
            command=project.get("command", ""),
            port=port,
        )
        level = "success" if ok else "warning"
        self._log(message, level)
        if ok:
            self.after(0, lambda: self.app_rows[project_id].set_status("active"))
            self.after(0, self._update_counts)
        elif project_id in self.app_rows:
            self.after(0, lambda: self.app_rows[project_id].set_status("conflict"))

    def _stop_project_async(self, project_id: str) -> None:
        threading.Thread(
            target=self._stop_project,
            args=(project_id,),
            daemon=True,
            name=f"stop-{project_id}",
        ).start()

    def _stop_project(self, project_id: str) -> None:
        project = self.data_store.find_project(project_id)
        name = project.get("name", "Application") if project else "Application"
        ok, message = self.process_manager.stop(project_id, name)
        self._log(message, "success" if ok else "warning")
        if project and project_id in self.app_rows:
            port = int(project.get("port", 0))
            state = evaluate_port_state(port, False)
            self.after(0, lambda: self.app_rows[project_id].set_status(state))
        self.after(0, self._update_counts)

    def _start_all_async(self) -> None:
        threading.Thread(target=self._start_all, daemon=True, name="start-all").start()

    def _start_all(self) -> None:
        for project in self.data_store.get_active_projects():
            project_id = project.get("id", "")
            if not self.process_manager.is_running(project_id):
                self._start_project(project_id)

    def _stop_all_async(self) -> None:
        threading.Thread(target=self._stop_all, daemon=True, name="stop-all").start()

    def _stop_all(self) -> None:
        projects = self.data_store.get_active_projects()
        messages = self.process_manager.stop_all_projects(projects)
        for message in messages:
            self._log(message, "success")
        self.after(0, self._refresh_inventory)

    def _on_window_close(self) -> None:
        if self._closing:
            return
        self._closing = True

        def task() -> None:
            projects = self.data_store.get_active_projects()
            self.process_manager.stop_all_projects(projects)
            self.after(0, self.destroy)

        threading.Thread(target=task, daemon=True, name="shutdown").start()

    def _update_counts(self) -> None:
        projects = self.data_store.get_active_projects()
        running = sum(1 for p in projects if self.process_manager.is_running(p.get("id", "")))
        self.toolbar.update_counts(running, len(projects))

    def _open_console(self, project_id: str) -> None:
        existing = self.console_windows.get(project_id)
        if existing and existing.winfo_exists():
            existing.focus()
            return

        project = self.data_store.find_project(project_id)
        if not project:
            return
        history = self.process_manager.get_log_history(project_id)
        window = ConsoleWindow(
            self,
            project.get("name", "Application"),
            project_id,
            initial_lines=history,
        )
        self.console_windows[project_id] = window

    def _open_add_wizard(self) -> None:
        ProjectWizard(self, on_save=self._save_new_project)

    def _save_new_project(self, payload: dict) -> None:
        try:
            created = self.data_store.add_project(payload)
        except DataStoreError as exc:
            self._handle_db_error("Could not add application", exc)
            return
        self._refresh_inventory()
        self._log(f"Added application '{created.get('name')}'.", "success")

    def _menu_action(self, action: str, project_id: str) -> None:
        project = self.data_store.find_project(project_id)
        if not project:
            return

        if action == "open_dir":
            path = project.get("path", "")
            if os.path.isdir(path):
                os.startfile(path)
            else:
                messagebox.showerror("Directory Error", "Project directory was not found.", parent=self)
        elif action == "open_vscode":
            path = project.get("path", "")
            if os.path.isdir(path):
                subprocess.Popen(
                    ["code", "."],
                    cwd=path,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
            else:
                messagebox.showerror("VS Code", "Project directory was not found.", parent=self)
        elif action == "edit":
            ProjectWizard(
                self,
                on_save=lambda data: self._save_edit_project(project_id, data),
                project=project,
                exclude_id=project_id,
            )
        elif action == "archive":
            if self.process_manager.is_running(project_id):
                messagebox.showwarning(
                    "Archive Blocked",
                    "Stop the application before archiving it.",
                    parent=self,
                )
                return
            try:
                archived = self.data_store.archive_project(project_id)
            except DataStoreError as exc:
                self._handle_db_error("Could not archive application", exc)
                return
            if archived:
                self._refresh_inventory()
                self._log(f"Archived '{project.get('name')}'.", "success")

    def _save_edit_project(self, project_id: str, payload: dict) -> None:
        try:
            updated = self.data_store.update_project(project_id, payload)
        except DataStoreError as exc:
            self._handle_db_error("Could not update application", exc)
            return
        if updated:
            self._refresh_inventory()
            self._audit_ports()
            self._log(f"Updated '{updated.get('name')}'.", "success")
