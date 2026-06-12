from __future__ import annotations

import base64
import ipaddress
from typing import Any

from .models import Mesh, Peer, Settings


class ConfigError(Exception):
    pass


def load_settings(settings_doc: dict[str, Any]) -> Settings:
    interface_name = settings_doc.get("InterfaceName", "wg0")
    listen_port = settings_doc.get("ListenPort", 51820)
    persistent_keepalive = settings_doc.get("PersistentKeepalive", 25)

    if not isinstance(interface_name, str) or not interface_name.strip():
        raise ConfigError("settings.yaml: InterfaceName must be non-empty string")

    try:
        listen_port_int = int(listen_port)
    except (TypeError, ValueError):
        raise ConfigError("settings.yaml: ListenPort must be integer")

    if not 1 <= listen_port_int <= 65535:
        raise ConfigError("settings.yaml: ListenPort must be in range 1..65535")

    if persistent_keepalive is None:
        keepalive_int = None
    else:
        try:
            keepalive_int = int(persistent_keepalive)
        except (TypeError, ValueError):
            raise ConfigError("settings.yaml: PersistentKeepalive must be integer or null")

        if keepalive_int < 0:
            raise ConfigError("settings.yaml: PersistentKeepalive must be >= 0")

    return Settings(
        interface_name=interface_name,
        listen_port=listen_port_int,
        persistent_keepalive=keepalive_int,
    )


def load_peers(peers_doc: dict[str, Any]) -> dict[str, Peer]:
    raw_peers = peers_doc.get("peers")

    if not isinstance(raw_peers, dict) or not raw_peers:
        raise ConfigError("peers.yaml must contain non-empty mapping: peers:")

    peers: dict[str, Peer] = {}
    seen_addresses: dict[str, str] = {}

    for peer_id, raw_peer in raw_peers.items():
        if not isinstance(peer_id, str) or not peer_id.strip():
            raise ConfigError("peer id must be non-empty string")

        if not isinstance(raw_peer, dict):
            raise ConfigError(f"peer {peer_id}: value must be mapping")

        interface = raw_peer.get("Interface")
        if not isinstance(interface, dict):
            raise ConfigError(f"peer {peer_id}: missing Interface mapping")

        raw_address = interface.get("Address")
        if raw_address is None:
            raise ConfigError(f"peer {peer_id}: missing Interface.Address")

        addresses = [str(item) for item in _as_list(raw_address)]
        if not addresses:
            raise ConfigError(f"peer {peer_id}: Interface.Address is empty")

        for item in addresses:
            cidr = _validate_cidr(
                value=item,
                where=f"peer {peer_id}: Interface.Address",
            )

            previous_peer = seen_addresses.get(cidr)
            if previous_peer is not None:
                raise ConfigError(
                    f"duplicate Interface.Address {cidr}: "
                    f"{previous_peer} and {peer_id}"
                )

            seen_addresses[cidr] = peer_id

        private_key = interface.get("PrivateKey")
        if not isinstance(private_key, str) or not private_key.strip():
            raise ConfigError(f"peer {peer_id}: missing Interface.PrivateKey")

        _validate_wg_key_shape(
            private_key,
            where=f"peer {peer_id}: Interface.PrivateKey",
        )

        endpoint = raw_peer.get("Endpoint")
        if endpoint is not None and not isinstance(endpoint, str):
            raise ConfigError(f"peer {peer_id}: Endpoint must be string or null")

        endpoint_port = raw_peer.get("EndpointPort")
        endpoint_port_int: int | None = None

        if endpoint_port is not None:
            if endpoint is None:
                raise ConfigError(
                    f"peer {peer_id}: EndpointPort is set but Endpoint is null"
                )

            try:
                endpoint_port_int = int(endpoint_port)
            except (TypeError, ValueError):
                raise ConfigError(f"peer {peer_id}: EndpointPort must be integer")

            if not 1 <= endpoint_port_int <= 65535:
                raise ConfigError(
                    f"peer {peer_id}: EndpointPort must be in range 1..65535"
                )

        raw_allowed_ips = raw_peer.get("AllowedIPs", [])
        if raw_allowed_ips is None:
            raw_allowed_ips = []

        if not isinstance(raw_allowed_ips, list):
            raise ConfigError(f"peer {peer_id}: AllowedIPs must be list")

        allowed_ips = [str(item) for item in raw_allowed_ips]

        for item in allowed_ips:
            _validate_cidr(
                value=item,
                where=f"peer {peer_id}: AllowedIPs",
            )

        peers[peer_id] = Peer(
            id=peer_id,
            address=addresses,
            private_key=private_key,
            endpoint=endpoint,
            endpoint_port=endpoint_port_int,
            allowed_ips=allowed_ips,
        )

    return peers


def load_mesh(mesh_doc: dict[str, Any], peers: dict[str, Peer]) -> Mesh:
    raw_mesh = mesh_doc.get("mesh", {}) or {}

    if not isinstance(raw_mesh, dict):
        raise ConfigError("mesh.yaml: mesh must be mapping")

    links: dict[str, dict[str, str]] = {}

    for peer_id, peer_mesh in raw_mesh.items():
        if peer_id not in peers:
            raise ConfigError(f"mesh.yaml: unknown peer {peer_id}")

        if peer_mesh is None:
            peer_mesh = {}

        if not isinstance(peer_mesh, dict):
            raise ConfigError(f"mesh.yaml: {peer_id} value must be mapping")

        links[peer_id] = {}

        for remote_id, value in peer_mesh.items():
            if remote_id not in peers:
                raise ConfigError(f"mesh.yaml: unknown remote peer {peer_id} -> {remote_id}")

            if remote_id == peer_id:
                raise ConfigError(f"mesh.yaml: self-link is not allowed: {peer_id}")

            if not isinstance(value, str) or not value.strip():
                raise ConfigError(f"mesh.yaml: empty PSK {peer_id} -> {remote_id}")

            _validate_wg_key_shape(
                value,
                where=f"mesh.yaml: {peer_id} -> {remote_id}",
            )

            links[peer_id][remote_id] = value

    for peer_id, peer_mesh in links.items():
        for remote_id, value in peer_mesh.items():
            reverse = links.get(remote_id, {}).get(peer_id)
            if reverse is None:
                raise ConfigError(
                    f"mesh.yaml: missing reverse link {remote_id} -> {peer_id}"
                )

            if reverse != value:
                raise ConfigError(
                    f"mesh.yaml: PSK mismatch {peer_id} <-> {remote_id}"
                )

    return Mesh(peers=peers, links=links)


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value]


def _validate_cidr(value: Any, where: str) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{where}: CIDR must be string")

    try:
        ipaddress.ip_network(value, strict=False)
        return value
    except ValueError as exc:
        raise ConfigError(f"{where}: invalid CIDR {value!r}: {exc}") from exc


def _validate_wg_key_shape(value: str, where: str) -> None:
    try:
        raw = base64.b64decode(value.strip(), validate=True)
    except Exception as exc:
        raise ConfigError(f"{where}: invalid base64 WireGuard key") from exc

    if len(raw) != 32:
        raise ConfigError(f"{where}: WireGuard key must decode to 32 bytes")
