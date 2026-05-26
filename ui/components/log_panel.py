"""System status log panel at the bottom of the dashboard."""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from ui.theme import (
    BG_LOG,
    BORDER,
    CORNER_RADIUS,
    FONT_FAMILY,
    FONT_MONO,
    LOG_INFO,
    LOG_SUCCESS,
    LOG_WARNING,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class LogPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            header,
            text="● System Status Logs",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=LOG_SUCCESS,
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="🗑 Clear",
            width=64,
            height=22,
            fg_color="transparent",
            hover_color=BORDER,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT_SECONDARY,
            corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, 9),
            command=self.clear,
        ).pack(side="right")

        self.textbox = ctk.CTkTextbox(
            self,
            height=96,
            fg_color=BG_LOG,
            border_color=BORDER,
            border_width=1,
            corner_radius=CORNER_RADIUS,
            font=(FONT_MONO, 10),
            text_color=TEXT_PRIMARY,
            wrap="word",
            activate_scrollbars=True,
        )
        self.textbox.pack(fill="both", expand=True)
        self.textbox.configure(state="disabled")
        self._auto_scroll = True
        self.textbox.bind("<Enter>", lambda _e: self._bind_scroll_lock())
        self.textbox.bind("<Leave>", lambda _e: self._unbind_scroll_lock())

    def _bind_scroll_lock(self) -> None:
        self.textbox.bind("<MouseWheel>", self._on_wheel)

    def _unbind_scroll_lock(self) -> None:
        self.textbox.unbind("<MouseWheel>")

    def _on_wheel(self, event) -> str:
        widget = self.textbox._textbox
        yview = widget.yview()
        if event.delta < 0 and yview[1] < 0.999:
            self._auto_scroll = False
        elif event.delta > 0 and yview[0] <= 0.001:
            self._auto_scroll = True
        return "break"

    def append(self, message: str, level: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M")
        color = LOG_INFO
        if level == "success":
            color = LOG_SUCCESS
        elif level == "warning":
            color = LOG_WARNING

        self.textbox.configure(state="normal")
        self.textbox.insert("end", f"[{timestamp}] {message}\n")
        last_line = int(float(self.textbox.index("end-1c").split(".")[0]))
        self.textbox.tag_add(level, f"{last_line}.0", f"{last_line}.end")
        self.textbox.tag_config(level, foreground=color)
        if self._auto_scroll:
            self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self) -> None:
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
        self._auto_scroll = True
