"""Non-blocking socket port diagnostics."""

from __future__ import annotations

import socket
from typing import Literal

PortState = Literal["ready", "active", "conflict"]


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Return True when a TCP handshake succeeds on the target port."""
    if port <= 0 or port > 65535:
        return False

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.35)
        try:
            return probe.connect_ex((host, port)) == 0
        except OSError:
            return False


def evaluate_port_state(port: int, is_running: bool) -> PortState:
    """Derive dashboard badge state from runtime and socket audit."""
    if is_running:
        return "active"
    if is_port_in_use(port):
        return "conflict"
    return "ready"
