"""Global action toolbar with Start All, Stop All, and status counters."""

from __future__ import annotations

import customtkinter as ctk

from ui.theme import (
    ACCENT_BLUE,
    ACCENT_GREEN,
    ACCENT_ORANGE,
    BG_PRIMARY,
    BORDER,
    CORNER_RADIUS,
    FONT_FAMILY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class Toolbar(ctk.CTkFrame):
    def __init__(self, master, on_start_all, on_stop_all, on_add, **kwargs) -> None:
        super().__init__(master, fg_color=BG_PRIMARY, **kwargs)

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkButton(
            left,
            text="▶  Start All",
            width=96,
            height=28,
            fg_color=ACCENT_GREEN,
            hover_color="#276749",
            corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, 10, "bold"),
            command=on_start_all,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            left,
            text="■  Stop All",
            width=96,
            height=28,
            fg_color="transparent",
            hover_color=BORDER,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, 10),
            command=on_stop_all,
        ).pack(side="left")

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right")

        self.running_label = ctk.CTkLabel(
            right,
            text="● 0 running",
            font=(FONT_FAMILY, 10),
            text_color=ACCENT_GREEN,
        )
        self.running_label.pack(side="left", padx=(0, 12))

        self.total_label = ctk.CTkLabel(
            right,
            text="● 0 total",
            font=(FONT_FAMILY, 10),
            text_color=ACCENT_ORANGE,
        )
        self.total_label.pack(side="left", padx=(0, 14))

        ctk.CTkButton(
            right,
            text="+  Add New Application",
            width=158,
            height=28,
            fg_color=ACCENT_BLUE,
            hover_color="#005BB5",
            corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, 10, "bold"),
            command=on_add,
        ).pack(side="left")

    def update_counts(self, running: int, total: int) -> None:
        self.running_label.configure(text=f"● {running} running")
        self.total_label.configure(text=f"● {total} total")
