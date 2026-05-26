"""Add / edit application wizard modal."""

from __future__ import annotations

import os
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.port_checker import is_port_in_use
from ui.theme import (
    ACCENT_BLUE,
    ACCENT_GREEN,
    BG_CARD,
    BG_INPUT,
    BG_PRIMARY,
    BORDER,
    CORNER_RADIUS,
    FONT_FAMILY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class ProjectWizard(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        on_save,
        project: dict | None = None,
        exclude_id: str | None = None,
    ) -> None:
        super().__init__(master)
        self.on_save = on_save
        self.project = project
        self.exclude_id = exclude_id
        self.title("Edit Application" if project else "Add New Application")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=BG_PRIMARY)
        self.grab_set()

        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=CORNER_RADIUS)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        self.name_var = ctk.StringVar(value=(project or {}).get("name", ""))
        self.path_var = ctk.StringVar(value=(project or {}).get("path", ""))
        self.port_var = ctk.StringVar(value=str((project or {}).get("port", 8000)))
        self.command_var = ctk.StringVar(value=(project or {}).get("command", ""))
        self.icon_var = ctk.StringVar(value=(project or {}).get("icon", ""))

        self.port_status = ctk.CTkLabel(card, text="", font=(FONT_FAMILY, 9))
        self.port_status.pack(anchor="w", padx=14, pady=(0, 4))

        self._row(card, "Display Name", self.name_var)
        self._path_row(card)
        self._row(card, "Port", self.port_var, on_change=self._validate_port)
        self._row(card, "Launch Command", self.command_var)
        self._icon_row(card)

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=14, pady=(10, 14))

        ctk.CTkButton(
            footer,
            text="Cancel",
            width=90,
            height=30,
            fg_color="transparent",
            border_width=1,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            command=self.destroy,
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            footer,
            text="Save Application",
            width=130,
            height=30,
            fg_color=ACCENT_GREEN,
            hover_color="#276749",
            font=(FONT_FAMILY, 10, "bold"),
            command=self._save,
        ).pack(side="right")

        self.port_var.trace_add("write", lambda *_: self._validate_port())
        self._validate_port()

    def _row(self, parent, label: str, variable: ctk.StringVar, on_change=None) -> None:
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(wrap, text=label, font=(FONT_FAMILY, 10), text_color=TEXT_SECONDARY).pack(anchor="w")
        entry = ctk.CTkEntry(
            wrap,
            textvariable=variable,
            height=30,
            fg_color=BG_INPUT,
            border_color=BORDER,
            font=(FONT_FAMILY, 10),
        )
        entry.pack(fill="x", pady=(2, 0))
        if on_change:
            variable.trace_add("write", lambda *_: on_change())

    def _path_row(self, parent) -> None:
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(wrap, text="Project Directory", font=(FONT_FAMILY, 10), text_color=TEXT_SECONDARY).pack(
            anchor="w"
        )
        row = ctk.CTkFrame(wrap, fg_color="transparent")
        row.pack(fill="x", pady=(2, 0))
        ctk.CTkEntry(
            row,
            textvariable=self.path_var,
            height=30,
            fg_color=BG_INPUT,
            border_color=BORDER,
            font=(FONT_FAMILY, 10),
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(
            row,
            text="Browse",
            width=72,
            height=30,
            fg_color=ACCENT_BLUE,
            command=self._pick_directory,
        ).pack(side="right")

    def _icon_row(self, parent) -> None:
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(wrap, text="Icon (.png / .ico)", font=(FONT_FAMILY, 10), text_color=TEXT_SECONDARY).pack(
            anchor="w"
        )
        row = ctk.CTkFrame(wrap, fg_color="transparent")
        row.pack(fill="x", pady=(2, 0))
        ctk.CTkEntry(
            row,
            textvariable=self.icon_var,
            height=30,
            fg_color=BG_INPUT,
            border_color=BORDER,
            font=(FONT_FAMILY, 10),
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(
            row,
            text="Browse",
            width=72,
            height=30,
            fg_color=ACCENT_BLUE,
            command=self._pick_icon,
        ).pack(side="right")

    def _pick_directory(self) -> None:
        path = filedialog.askdirectory(parent=self, title="Select Project Directory")
        if path:
            self.path_var.set(path)

    def _pick_icon(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Select Application Icon",
            filetypes=[("Image files", "*.png *.ico"), ("All files", "*.*")],
        )
        if path:
            self.icon_var.set(path)

    def _validate_port(self) -> None:
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            self.port_status.configure(text="Enter a valid port number.", text_color="#F87171")
            return

        if port < 1 or port > 65535:
            self.port_status.configure(text="Port must be between 1 and 65535.", text_color="#F87171")
            return

        if is_port_in_use(port):
            self.port_status.configure(text=f"Warning: Port {port} appears to be in use.", text_color="#D97706")
        else:
            self.port_status.configure(text=f"Port {port} is available.", text_color="#3FB950")

    def _save(self) -> None:
        name = self.name_var.get().strip()
        path = self.path_var.get().strip()
        command = self.command_var.get().strip()
        icon = self.icon_var.get().strip()

        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            messagebox.showerror("Validation Error", "Port must be a number.", parent=self)
            return

        if not name:
            messagebox.showerror("Validation Error", "Display name is required.", parent=self)
            return
        if not path or not os.path.isdir(path):
            messagebox.showerror("Validation Error", "Select a valid project directory.", parent=self)
            return
        if not command:
            messagebox.showerror("Validation Error", "Launch command is required.", parent=self)
            return

        payload = {
            "name": name,
            "path": path,
            "port": port,
            "command": command,
            "icon": icon,
        }
        if self.project:
            payload["id"] = self.project.get("id")

        self.on_save(payload)
        self.destroy()
