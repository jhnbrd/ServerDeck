"""Isolated per-project console log viewer."""

from __future__ import annotations

import queue

import customtkinter as ctk

from ui.theme import (
    ACCENT_BLUE,
    BG_CARD,
    BG_LOG,
    BG_PRIMARY,
    BORDER,
    CORNER_RADIUS,
    FONT_FAMILY,
    FONT_MONO,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class ConsoleWindow(ctk.CTkToplevel):
    """Streams stdout/stderr lines without blocking the main UI thread."""

    def __init__(self, master, project_name: str, project_id: str) -> None:
        super().__init__(master)
        self.project_id = project_id
        self.title(f"Console — {project_name}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=BG_PRIMARY)

        self._queue: queue.Queue[str] = queue.Queue()
        self._auto_scroll = True
        self._closed = False

        toolbar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        toolbar.pack(fill="x", padx=12, pady=(12, 6))

        self.search_var = ctk.StringVar()
        ctk.CTkEntry(
            toolbar,
            placeholder_text="Search logs…",
            textvariable=self.search_var,
            width=220,
            height=28,
            fg_color=BG_LOG,
            border_color=BORDER,
            font=(FONT_FAMILY, 10),
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            toolbar,
            text="Find",
            width=56,
            height=28,
            fg_color=ACCENT_BLUE,
            font=(FONT_FAMILY, 10),
            command=self._search,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            toolbar,
            text="Clear",
            width=56,
            height=28,
            fg_color="transparent",
            border_width=1,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            font=(FONT_FAMILY, 10),
            command=self.clear,
        ).pack(side="left")
        self.autoscroll_btn = ctk.CTkButton(
            toolbar,
            text="Auto-scroll: ON",
            width=110,
            height=28,
            fg_color="transparent",
            border_width=1,
            border_color=BORDER,
            text_color=TEXT_SECONDARY,
            font=(FONT_FAMILY, 10),
            command=self._toggle_autoscroll,
        )
        self.autoscroll_btn.pack(side="right")

        self.textbox = ctk.CTkTextbox(
            self,
            fg_color=BG_LOG,
            border_color=BORDER,
            border_width=1,
            corner_radius=CORNER_RADIUS,
            font=(FONT_MONO, 10),
            text_color=TEXT_PRIMARY,
            wrap="none",
        )
        self.textbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.textbox.configure(state="disabled")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._poll_queue)

    def push_line(self, line: str) -> None:
        if not self._closed:
            self._queue.put(line)

    def clear(self) -> None:
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")

    def _toggle_autoscroll(self) -> None:
        self._auto_scroll = not self._auto_scroll
        label = "Auto-scroll: ON" if self._auto_scroll else "Auto-scroll: OFF"
        self.autoscroll_btn.configure(text=label)

    def _search(self) -> None:
        query = self.search_var.get().strip()
        if not query:
            return
        widget = self.textbox._textbox
        widget.tag_remove("search_hit", "1.0", "end")
        start = "1.0"
        while True:
            pos = widget.search(query, start, stopindex="end", nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            widget.tag_add("search_hit", pos, end)
            start = end
        widget.tag_config("search_hit", background="#3D2C00", foreground="#FFD580")
        first = widget.search(query, "1.0", stopindex="end", nocase=True)
        if first:
            widget.see(first)

    def _poll_queue(self) -> None:
        if self._closed:
            return
        updated = False
        while True:
            try:
                line = self._queue.get_nowait()
            except queue.Empty:
                break
            self.textbox.configure(state="normal")
            self.textbox.insert("end", line + "\n")
            updated = True
            self.textbox.configure(state="disabled")
        if updated and self._auto_scroll:
            self.textbox.see("end")
        self.after(120, self._poll_queue)

    def _on_close(self) -> None:
        self._closed = True
        self.destroy()
