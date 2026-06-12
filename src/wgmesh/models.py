from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    interface_name: str
    listen_port: int
    persistent_keepalive: int | None


@dataclass(frozen=True)
class Peer:
    id: str
    address: list[str]
    private_key: str
    endpoint: str | None
    endpoint_port: int | None
    allowed_ips: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Mesh:
    peers: dict[str, Peer]
    links: dict[str, dict[str, str]]
