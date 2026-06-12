from __future__ import annotations

import shutil
from pathlib import Path

from .generators import generate_extra_files
from .models import Mesh, Peer
from .resources import package_templates_dir
from .validate import load_mesh, load_peers, load_settings
from .wg import get_wg
from .yamlio import load_yaml


def build_configs(
    mesh_dir: Path,
    output_dir: Path,
    templates_dir: Path | None,
    clean: bool = False,
    dry_run: bool = False,
) -> None:
    templates_dir = templates_dir or package_templates_dir()

    settings_doc = load_yaml(mesh_dir / "settings.yaml", required=False)
    peers_doc = load_yaml(mesh_dir / "peers.yaml", required=True)
    mesh_doc = load_yaml(mesh_dir / "mesh.yaml", required=False)

    settings = load_settings(settings_doc)
    peers = load_peers(peers_doc)
    mesh = load_mesh(mesh_doc, peers)

    wg = get_wg()

    public_keys = {
        peer_id: wg.pubkey(peer.private_key)
        for peer_id, peer in mesh.peers.items()
    }

    rendered: dict[str, dict[str, str]] = {}

    for peer_id in sorted(mesh.peers):
        peer = mesh.peers[peer_id]
        route_targets = collect_peer_route_targets(peer_id, mesh)

        peer_files = {
            f"{settings.interface_name}.conf": render_config(
                peer=peer,
                mesh=mesh,
                public_keys=public_keys,
                listen_port=settings.listen_port,
                persistent_keepalive=settings.persistent_keepalive,
            ),
        }

        peer_files.update(
            generate_extra_files(
                templates_dir=templates_dir,
                peer_id=peer_id,
                interface_name=settings.interface_name,
                routes=route_targets,
            )
        )

        rendered[peer_id] = peer_files

    if not dry_run:
        if clean and output_dir.exists():
            shutil.rmtree(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        for peer_id, files in rendered.items():
            peer_dir = output_dir / peer_id
            peer_dir.mkdir(parents=True, exist_ok=True)

            for filename, content in files.items():
                path = peer_dir / filename
                path.write_text(content, encoding="utf-8")
                print(f"generated: {path}")

    print_summary(mesh=mesh, rendered=rendered, dry_run=dry_run)


def render_config(
    peer: Peer,
    mesh: Mesh,
    public_keys: dict[str, str],
    listen_port: int,
    persistent_keepalive: int | None,
) -> str:
    lines: list[str] = []

    lines.append("[Interface]")
    lines.append(f"Address = {format_address(peer.address)}")
    lines.append(f"PrivateKey = {peer.private_key}")
    lines.append("")

    for remote_id in sorted(mesh.links.get(peer.id, {})):
        remote = mesh.peers[remote_id]

        lines.append("[Peer]")
        lines.append(f"# {remote_id}")
        lines.append(f"PublicKey = {public_keys[remote_id]}")
        lines.append(f"PresharedKey = {mesh.links[peer.id][remote_id]}")

        if remote.endpoint:
            port = remote.endpoint_port if remote.endpoint_port is not None else listen_port
            lines.append(f"Endpoint = {remote.endpoint}:{port}")

        lines.append(f"AllowedIPs = {','.join(collect_allowed_ips(remote))}")

        if persistent_keepalive is not None:
            lines.append(f"PersistentKeepalive = {persistent_keepalive}")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def collect_peer_route_targets(peer_id: str, mesh: Mesh) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for remote_id in sorted(mesh.links.get(peer_id, {})):
        for item in collect_allowed_ips(mesh.peers[remote_id]):
            if item not in seen:
                seen.add(item)
                result.append(item)

    return result


def format_address(address: list[str]) -> str:
    return ",".join(address)


def collect_allowed_ips(peer: Peer) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        if value not in seen:
            seen.add(value)
            result.append(value)

    for item in peer.address:
        add(item)

    for item in peer.allowed_ips:
        add(item)

    return result


def print_summary(
    mesh: Mesh,
    rendered: dict[str, dict[str, str]],
    dry_run: bool,
) -> None:
    mesh_entries = sum(len(v) for v in mesh.links.values())
    files_count = sum(len(v) for v in rendered.values())
    prefix = "dry-run: " if dry_run else ""

    print("")
    print(f"{prefix}peers: {len(mesh.peers)}")
    print(f"{prefix}mesh entries: {mesh_entries}")
    print(f"{prefix}generated peers: {len(rendered)}")
    print(f"{prefix}generated files: {files_count}")
