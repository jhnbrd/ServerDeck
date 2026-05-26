"""Network configuration header panel."""

from __future__ import annotations

import customtkinter as ctk

from ui.theme import (
    ACCENT_BLUE,
    BG_CARD,
    BG_INPUT,
    BORDER,
    CORNER_RADIUS,
    FONT_FAMILY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class NetworkPanel(ctk.CTkFrame):
    def __init__(self, master, on_apply, **kwargs) -> None:
        super().__init__(master, fg_color=BG_CARD, corner_radius=CORNER_RADIUS, **kwargs)
        self.on_apply = on_apply

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            inner,
            text="⬡ Network",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.ip_var = ctk.StringVar(value="192.168.1.10")
        self.subnet_var = ctk.StringVar(value="255.255.255.0")
        self.gateway_var = ctk.StringVar(value="192.168.1.1")
        self.adapter_var = ctk.StringVar(value="Ethernet")

        self._field(inner, "IP", self.ip_var, 0, 1, width=108)
        self._field(inner, "Subnet", self.subnet_var, 0, 2, width=108)
        self._field(inner, "Gateway", self.gateway_var, 0, 3, width=108)

        adapter_wrap = ctk.CTkFrame(inner, fg_color="transparent")
        adapter_wrap.grid(row=0, column=4, padx=(0, 8), sticky="w")
        ctk.CTkLabel(adapter_wrap, text="Adapter", font=(FONT_FAMILY, 9), text_color=TEXT_SECONDARY).pack(
            anchor="w"
        )
        self.adapter_menu = ctk.CTkOptionMenu(
            adapter_wrap,
            variable=self.adapter_var,
            values=["Ethernet"],
            width=108,
            height=26,
            fg_color=BG_INPUT,
            button_color=BORDER,
            button_hover_color=ACCENT_BLUE,
            dropdown_fg_color=BG_INPUT,
            font=(FONT_FAMILY, 10),
        )
        self.adapter_menu.pack()

        ctk.CTkButton(
            inner,
            text="✓ Apply Network",
            width=118,
            height=28,
            fg_color=ACCENT_BLUE,
            hover_color="#005BB5",
            corner_radius=CORNER_RADIUS,
            font=(FONT_FAMILY, 10, "bold"),
            command=self._apply,
        ).grid(row=0, column=5, padx=(4, 0), sticky="e")

        inner.grid_columnconfigure(5, weight=1)

    def _field(self, parent, label: str, variable: ctk.StringVar, row: int, col: int, width: int) -> None:
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=col, padx=(0, 8), sticky="w")
        ctk.CTkLabel(wrap, text=label, font=(FONT_FAMILY, 9), text_color=TEXT_SECONDARY).pack(anchor="w")
        ctk.CTkEntry(
            wrap,
            textvariable=variable,
            width=width,
            height=26,
            fg_color=BG_INPUT,
            border_color=BORDER,
            font=(FONT_FAMILY, 10),
        ).pack()

    def set_adapters(self, names: list[str], selected: str | None = None) -> None:
        if not names:
            names = ["Ethernet"]
        self.adapter_menu.configure(values=names)
        if selected and selected in names:
            self.adapter_var.set(selected)
        else:
            self.adapter_var.set(names[0])

    def set_values(self, ip: str, subnet: str, gateway: str) -> None:
        if ip:
            self.ip_var.set(ip)
        if subnet:
            self.subnet_var.set(subnet)
        if gateway:
            self.gateway_var.set(gateway)

    def _apply(self) -> None:
        self.on_apply(
            self.adapter_var.get(),
            self.ip_var.get().strip(),
            self.subnet_var.get().strip(),
            self.gateway_var.get().strip(),
        )
