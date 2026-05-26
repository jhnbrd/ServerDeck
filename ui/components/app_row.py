"""Single application inventory row."""

from __future__ import annotations

import os
from typing import Callable

import customtkinter as ctk
from PIL import Image

from ui.theme import (
    ACCENT_GREEN,
    ACCENT_GREEN_BRIGHT,
    ACCENT_ORANGE,
    BG_CARD,
    BG_INPUT,
    BORDER,
    CORNER_RADIUS,
    FONT_FAMILY,
    ROW_HEIGHT,
    STATUS_ACTIVE_BG,
    STATUS_ACTIVE_FG,
    STATUS_CONFLICT_BG,
    STATUS_CONFLICT_FG,
    STATUS_READY_BG,
    STATUS_READY_FG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

ICON_COLORS = ["#F97316", "#A855F7", "#3B82F6", "#22C55E", "#EF4444", "#6B7280", "#FB923C"]


class AppRow(ctk.CTkFrame):
    def __init__(
        self,
        master,
        project: dict,
        index: int,
        on_start,
        on_stop,
        on_console,
        on_menu_action: Callable[[str, str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=BG_CARD, corner_radius=CORNER_RADIUS, height=ROW_HEIGHT, **kwargs)
        self.pack_propagate(False)
        self.project = project
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_console = on_console
        self.on_menu_action = on_menu_action

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8, pady=4)

        self.icon_label = ctk.CTkLabel(inner, text="", width=22, height=22)
        self.icon_label.grid(row=0, column=0, padx=(0, 6), sticky="w")
        self._set_icon(project, index)

        self.name_label = ctk.CTkLabel(
            inner,
            text=project.get("name", "Untitled"),
            font=(FONT_FAMILY, 11, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
            width=168,
        )
        self.name_label.grid(row=0, column=1, sticky="w")

        port = project.get("port", 0)
        self.port_badge = ctk.CTkLabel(
            inner,
            text=f"📶 :{port}",
            font=(FONT_FAMILY, 9),
            text_color=TEXT_SECONDARY,
            fg_color=BG_INPUT,
            corner_radius=10,
            width=62,
            height=22,
        )
        self.port_badge.grid(row=0, column=2, padx=(4, 8))

        self.status_badge = ctk.CTkLabel(
            inner,
            text="● Ready",
            font=(FONT_FAMILY, 9, "bold"),
            width=72,
            height=22,
            corner_radius=10,
        )
        self.status_badge.grid(row=0, column=3, padx=(0, 8))

        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.grid(row=0, column=4, sticky="e")

        self.primary_btn = ctk.CTkButton(
            actions,
            text="Start",
            width=58,
            height=24,
            corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, 9, "bold"),
            command=self._primary_action,
        )
        self.primary_btn.pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            actions,
            text=">_ Console",
            width=78,
            height=24,
            fg_color="transparent",
            hover_color=BORDER,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, 9),
            command=lambda: on_console(project.get("id", "")),
        ).pack(side="left", padx=(0, 4))

        self.menu_btn = ctk.CTkButton(
            actions,
            text="•••",
            width=32,
            height=24,
            fg_color="transparent",
            hover_color=BORDER,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, 10, "bold"),
            command=self._open_menu,
        )
        self.menu_btn.pack(side="left")

        inner.grid_columnconfigure(1, weight=1)

        self.set_status(project.get("status", "ready"))

    def _set_icon(self, project: dict, index: int) -> None:
        icon_path = project.get("icon") or ""
        if icon_path and os.path.isfile(icon_path):
            try:
                img = Image.open(icon_path).resize((18, 18))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(18, 18))
                self.icon_label.configure(image=ctk_img, text="")
                self.icon_label.image = ctk_img
                return
            except OSError:
                pass

        color = ICON_COLORS[index % len(ICON_COLORS)]
        self.icon_label.configure(
            text="◆",
            text_color=color,
            fg_color=BG_INPUT,
            corner_radius=4,
            width=22,
            height=22,
        )

    def set_status(self, status: str) -> None:
        self.project["status"] = status
        if status == "active":
            self.status_badge.configure(
                text="● Active",
                fg_color=STATUS_ACTIVE_BG,
                text_color=STATUS_ACTIVE_FG,
            )
            self.primary_btn.configure(
                text="Stop",
                fg_color="transparent",
                hover_color=BORDER,
                border_width=1,
                border_color=BORDER,
                text_color=TEXT_PRIMARY,
                command=self._stop,
            )
        elif status == "conflict":
            self.status_badge.configure(
                text="● Conflict",
                fg_color=STATUS_CONFLICT_BG,
                text_color=STATUS_CONFLICT_FG,
            )
            self.primary_btn.configure(
                text="🔧 Fix",
                fg_color="transparent",
                hover_color=STATUS_CONFLICT_BG,
                border_width=1,
                border_color=ACCENT_ORANGE,
                text_color=ACCENT_ORANGE,
                command=self._fix,
            )
        else:
            self.status_badge.configure(
                text="● Ready",
                fg_color=STATUS_READY_BG,
                text_color=STATUS_READY_FG,
            )
            self.primary_btn.configure(
                text="Start",
                fg_color=ACCENT_GREEN_BRIGHT,
                hover_color=ACCENT_GREEN,
                border_width=0,
                text_color="#FFFFFF",
                command=self._start,
            )

    def _primary_action(self) -> None:
        status = self.project.get("status", "ready")
        if status == "active":
            self._stop()
        elif status == "conflict":
            self._fix()
        else:
            self._start()

    def _start(self) -> None:
        self.on_start(self.project.get("id", ""))

    def _stop(self) -> None:
        self.on_stop(self.project.get("id", ""))

    def _fix(self) -> None:
        self.on_menu_action("edit", self.project.get("id", ""))

    def _open_menu(self) -> None:
        menu = ctk.CTkToplevel(self)
        menu.title("")
        menu.geometry("180x148")
        menu.resizable(False, False)
        menu.attributes("-topmost", True)
        menu.configure(fg_color=BG_CARD)

        x = self.menu_btn.winfo_rootx() - 140
        y = self.menu_btn.winfo_rooty() + 26
        menu.geometry(f"+{x}+{y}")

        pid = self.project.get("id", "")

        def act(action: str) -> None:
            menu.destroy()
            self.on_menu_action(action, pid)

        for label, action in [
            ("Open Directory", "open_dir"),
            ("Open in VS Code", "open_vscode"),
            ("Edit Application", "edit"),
            ("Move to Archive", "archive"),
        ]:
            ctk.CTkButton(
                menu,
                text=label,
                anchor="w",
                fg_color="transparent",
                hover_color=BORDER,
                text_color=TEXT_PRIMARY,
                font=(FONT_FAMILY, 10),
                command=lambda a=action: act(a),
            ).pack(fill="x", padx=6, pady=2)
