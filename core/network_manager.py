"""Network adapter discovery and static IP configuration."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass


@dataclass
class AdapterInfo:
    name: str
    ip: str = ""
    subnet: str = ""
    gateway: str = ""


def list_adapters() -> list[AdapterInfo]:
    """Return Windows network adapters with current IPv4 settings."""
    adapters: list[AdapterInfo] = []
    try:
        result = subprocess.run(
            ["netsh", "interface", "ipv4", "show", "config"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except OSError:
        return [AdapterInfo(name="Ethernet")]

    current: AdapterInfo | None = None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Configuration for interface"):
            match = re.search(r'"([^"]+)"', stripped)
            if match:
                if current:
                    adapters.append(current)
                current = AdapterInfo(name=match.group(1))
            continue

        if not current:
            continue

        if stripped.startswith("IP Address:"):
            current.ip = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Subnet Prefix:"):
            prefix = stripped.split(":", 1)[1].strip().split()[0]
            current.subnet = _prefix_to_mask(prefix)
        elif stripped.startswith("Subnet Mask:"):
            current.subnet = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Default Gateway:"):
            gateway = stripped.split(":", 1)[1].strip()
            if gateway and gateway.lower() != "none":
                current.gateway = gateway.split()[0]

    if current:
        adapters.append(current)

    return adapters or [AdapterInfo(name="Ethernet")]


def _prefix_to_mask(prefix: str) -> str:
    try:
        bits = int(prefix.replace("(", "").replace(")", "").split("/")[-1])
        mask = (0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF
        return ".".join(str((mask >> shift) & 0xFF) for shift in (24, 16, 8, 0))
    except (TypeError, ValueError):
        return "255.255.255.0"


def apply_static_ip(adapter: str, ip: str, subnet: str, gateway: str) -> tuple[bool, str]:
    """Apply static IPv4 settings via netsh."""
    command = [
        "netsh",
        "interface",
        "ip",
        "set",
        "address",
        f'name="{adapter}"',
        "static",
        ip,
        subnet,
        gateway,
        "1",
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except OSError as exc:
        return False, str(exc)

    if result.returncode == 0:
        return True, "Network configuration applied successfully."

    combined = f"{result.stdout}\n{result.stderr}".lower()
    if "access is denied" in combined or "denied" in combined:
        return (
            False,
            "Administrator privileges are required. Please launch ServerDeck as Administrator.",
        )
    return False, result.stderr.strip() or result.stdout.strip() or "Unable to apply network settings."
