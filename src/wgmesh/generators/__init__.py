from __future__ import annotations

from pathlib import Path
from typing import Any

from .routes import generate_route_files


def generate_extra_files(
    *,
    templates_dir: Path,
    peer_id: str,
    interface_name: str,
    routes: list[str],
) -> dict[str, str]:
    """Generate non-WireGuard extra artifacts for one peer.

    Keep this function intentionally small: future generators
    (firewall, nftables, bgp, etc.) can be plugged here in the
    same way as routes.
    """

    files: dict[str, str] = {}

    files.update(
        generate_route_files(
            templates_dir=templates_dir,
            peer_id=peer_id,
            interface_name=interface_name,
            routes=routes,
        )
    )

    return files
