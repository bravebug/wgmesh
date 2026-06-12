from __future__ import annotations

from pathlib import Path
from typing import Any

from .wg import get_wg
from .yamlio import load_yaml, save_yaml


def fill_nulls(
    mesh_dir: Path,
    *,
    run_build: bool = False,
    output_dir: Path | None = None,
    templates_dir: Path | None = None,
) -> None:
    peers_path = mesh_dir / "peers.yaml"
    mesh_path = mesh_dir / "mesh.yaml"

    peers_doc = load_yaml(peers_path, required=True)
    mesh_doc = load_yaml(mesh_path, required=False)

    wg = get_wg()

    changed_peers = fill_peer_keys(peers_doc, wg)
    changed_mesh = fill_mesh_keys(mesh_doc, wg)

    if changed_peers:
        save_yaml(peers_path, peers_doc)

    if changed_mesh:
        save_yaml(mesh_path, mesh_doc)

    print(f"filled PrivateKey: {changed_peers}")
    print(f"filled mesh PSK: {changed_mesh}")

    if run_build:
        from .build import build_configs

        build_configs(
            mesh_dir=mesh_dir,
            output_dir=output_dir or Path("generated"),
            templates_dir=templates_dir or Path("templates"),
            clean=False,
        )


def fill_peer_keys(peers_doc: dict[str, Any], wg) -> int:
    peers = peers_doc.get("peers", {})
    if not isinstance(peers, dict):
        return 0

    count = 0

    for peer in peers.values():
        if not isinstance(peer, dict):
            continue

        interface = peer.get("Interface")
        if not isinstance(interface, dict):
            continue

        if "PrivateKey" in interface and interface["PrivateKey"] is None:
            interface["PrivateKey"] = wg.genkey()
            count += 1

    return count


def fill_mesh_keys(mesh_doc: dict[str, Any], wg) -> int:
    mesh = mesh_doc.get("mesh")
    if mesh is None:
        return 0

    if not isinstance(mesh, dict):
        return 0

    generated_pairs: dict[tuple[str, str], str] = {}
    count = 0

    for peer_id, peer_mesh in list(mesh.items()):
        if not isinstance(peer_mesh, dict):
            continue

        for remote_id, value in list(peer_mesh.items()):
            if value is not None:
                continue

            pair = tuple(sorted((str(peer_id), str(remote_id))))
            key = generated_pairs.get(pair)

            if key is None:
                reverse_value = (
                    mesh.get(remote_id, {}).get(peer_id)
                    if isinstance(mesh.get(remote_id), dict)
                    else None
                )

                if reverse_value is not None:
                    key = reverse_value
                else:
                    key = wg.genpsk()

                generated_pairs[pair] = key

            peer_mesh[remote_id] = key
            count += 1

            reverse = mesh.get(remote_id)
            if isinstance(reverse, dict) and reverse.get(peer_id) is None:
                reverse[peer_id] = key
                count += 1

    return count
